"""
Anthropic Provider Implementation
"""
import asyncio
from typing import List
from anthropic import AsyncAnthropic, APIConnectionError, APITimeoutError
import structlog

from app.services.ai_provider import BaseAIProvider, AIMessage, AIResponse
from app.core.config import settings

logger = structlog.get_logger()

# Errors that are safe to retry (transient network/infra issues)
_RETRYABLE_ERRORS = (APITimeoutError, APIConnectionError)
_MAX_RETRIES = 2
_RETRY_BACKOFF = 2.0  # seconds before first retry; doubles each attempt


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic API provider

    Supports Claude 3.5 Sonnet, Claude 3 Opus, etc.
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key, timeout=settings.AI_TIMEOUT)

    async def chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """
        Generate chat completion using Anthropic

        Args:
            messages: List of messages
            temperature: Sampling temperature (0-1 for Anthropic)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic parameters

        Returns:
            AIResponse with generated content
        """
        # Separate system messages from user/assistant messages once —
        # this is the same for every attempt so do it outside the retry loop.
        system_content = None
        conversation_messages = []
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                conversation_messages.append({"role": msg.role, "content": msg.content})

        request_params = {
            "model": self.model,
            "messages": conversation_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        if system_content:
            request_params["system"] = system_content

        last_error: Exception = RuntimeError("No attempts made")
        for attempt in range(1 + _MAX_RETRIES):
            if attempt > 0:
                delay = _RETRY_BACKOFF * (2 ** (attempt - 1))
                self.logger.warning(
                    "Retrying Anthropic completion",
                    attempt=attempt,
                    delay=delay,
                    error=str(last_error),
                    model=self.model,
                )
                await asyncio.sleep(delay)

            try:
                self.logger.info(
                    "Requesting Anthropic completion",
                    model=self.model,
                    message_count=len(conversation_messages),
                    has_system=system_content is not None,
                )

                response = await self.client.messages.create(**request_params)

                content = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                finish_reason = response.stop_reason

                self.logger.info(
                    "Anthropic completion successful",
                    model=self.model,
                    tokens=tokens_used,
                    finish_reason=finish_reason,
                )

                return AIResponse(
                    content=content,
                    model=self.model,
                    provider="anthropic",
                    tokens_used=tokens_used,
                    finish_reason=finish_reason,
                    metadata={
                        "response_id": response.id,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    }
                )

            except _RETRYABLE_ERRORS as e:
                last_error = e
                self.logger.error(
                    "Anthropic completion failed (retryable)",
                    error=str(e),
                    model=self.model,
                    attempt=attempt,
                )
            except Exception as e:
                # Non-retryable (auth errors, bad requests, etc.) — fail immediately
                self.logger.error(
                    "Anthropic completion failed",
                    error=str(e),
                    model=self.model,
                )
                raise

        raise last_error

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "anthropic"
