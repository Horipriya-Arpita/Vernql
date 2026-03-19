"""
AI Client Service
Supports both OpenAI and Anthropic APIs with automatic fallback
"""
from typing import Optional, Dict, Any, List
import structlog
from openai import OpenAI, OpenAIError
from anthropic import Anthropic, AnthropicError

from app.core.config import settings

logger = structlog.get_logger()


class AIClient:
    """
    Unified AI client that supports both OpenAI and Anthropic
    Primary provider: OpenAI
    Fallback provider: Anthropic (if configured)
    """

    def __init__(self):
        self.primary_provider = settings.DEFAULT_AI_PROVIDER
        self.default_model = settings.DEFAULT_AI_MODEL

        # Initialize OpenAI client
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.AI_TIMEOUT
            )
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not configured")

        # Initialize Anthropic client (optional fallback)
        self.anthropic_client = None
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=settings.AI_TIMEOUT
            )
            logger.info("Anthropic client initialized (fallback)")

    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> str:
        """
        Generate AI completion using primary provider with automatic fallback

        Args:
            prompt: User prompt
            system_prompt: System instruction
            model: Model to use (overrides default)
            temperature: Randomness (0.0 to 1.0)
            max_tokens: Maximum response tokens
            json_mode: Force JSON response format

        Returns:
            Generated text response

        Raises:
            Exception: If both providers fail
        """
        model = model or self.default_model

        # Try primary provider first
        if self.primary_provider == "openai" and self.openai_client:
            try:
                return self._generate_openai(
                    prompt, system_prompt, model, temperature, max_tokens, json_mode
                )
            except Exception as e:
                logger.error("OpenAI generation failed", error=str(e))
                # Try Anthropic fallback if available
                if self.anthropic_client:
                    logger.info("Falling back to Anthropic")
                    return self._generate_anthropic(
                        prompt, system_prompt, None, temperature, max_tokens
                    )
                raise

        elif self.primary_provider == "anthropic" and self.anthropic_client:
            try:
                return self._generate_anthropic(
                    prompt, system_prompt, model, temperature, max_tokens
                )
            except Exception as e:
                logger.error("Anthropic generation failed", error=str(e))
                # Try OpenAI fallback if available
                if self.openai_client:
                    logger.info("Falling back to OpenAI")
                    return self._generate_openai(
                        prompt, system_prompt, None, temperature, max_tokens, json_mode
                    )
                raise

        else:
            raise ValueError(
                f"No AI provider configured. Primary: {self.primary_provider}, "
                f"OpenAI: {'yes' if self.openai_client else 'no'}, "
                f"Anthropic: {'yes' if self.anthropic_client else 'no'}"
            )

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> str:
        """Generate completion using OpenAI API"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        # Use gpt-4o if no model specified
        model = model or "gpt-4o"

        response_format = {"type": "json_object"} if json_mode else {"type": "text"}

        logger.info("Calling OpenAI API", model=model, tokens=max_tokens)

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )

        content = response.choices[0].message.content
        logger.info("OpenAI response received", length=len(content))

        return content

    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate completion using Anthropic API"""
        # Use Claude 3.5 Sonnet if no model specified
        model = model or "claude-3-5-sonnet-20241022"

        logger.info("Calling Anthropic API", model=model, tokens=max_tokens)

        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        content = response.content[0].text
        logger.info("Anthropic response received", length=len(content))

        return content

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of AI providers

        Returns:
            Dict with status of each provider
        """
        status = {
            "primary_provider": self.primary_provider,
            "openai": {
                "configured": self.openai_client is not None,
                "healthy": False
            },
            "anthropic": {
                "configured": self.anthropic_client is not None,
                "healthy": False
            }
        }

        # Test OpenAI
        if self.openai_client:
            try:
                self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                status["openai"]["healthy"] = True
            except Exception as e:
                logger.error("OpenAI health check failed", error=str(e))

        # Test Anthropic
        if self.anthropic_client:
            try:
                self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=5,
                    messages=[{"role": "user", "content": "test"}]
                )
                status["anthropic"]["healthy"] = True
            except Exception as e:
                logger.error("Anthropic health check failed", error=str(e))

        return status


# Global AI client instance
ai_client = AIClient()
