"""
OpenAI Provider Implementation
"""
from typing import List
from openai import AsyncOpenAI
import structlog

from app.services.ai_provider import BaseAIProvider, AIMessage, AIResponse

logger = structlog.get_logger()


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API provider

    Supports GPT-4, GPT-4 Turbo, GPT-3.5, etc.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)

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
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            self.logger.info(
                "Requesting OpenAI completion",
                model=self.model,
                message_count=len(messages)
            )

            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            # Extract response
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

        except Exception as e:
            self.logger.error(
                "OpenAI completion failed",
                error=str(e),
                model=self.model
            )
            raise

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "openai"
