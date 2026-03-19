"""
Rate limiting middleware using Redis
"""
import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis token bucket algorithm

    Implements per-API-key rate limiting with sliding window

    Security: Fails closed when Redis is unavailable to prevent rate limit bypass
    """

    def __init__(self, app, redis_client: redis.Redis = None):
        super().__init__(app)
        self.redis_client = redis_client or self._create_redis_client()
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.redis_available = self._test_redis_connection()

    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client from settings"""
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            logger.info("Redis client created for rate limiting")
            return client
        except Exception as e:
            logger.error("Failed to create Redis client", error=str(e))
            # Return None - will be handled in _test_redis_connection
            return None

    def _test_redis_connection(self) -> bool:
        """Test Redis connection and return availability status"""
        if self.redis_client is None:
            logger.warning("Redis client is None - rate limiting will fail closed")
            return False

        try:
            self.redis_client.ping()
            logger.info("Redis connection test successful")
            return True
        except Exception as e:
            logger.error("Redis connection test failed", error=str(e))
            return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and apply rate limiting

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            # No API key, skip rate limiting (will fail auth later)
            return await call_next(request)

        # Check rate limits
        try:
            self._check_rate_limit(api_key)
        except HTTPException:
            raise
        except Exception as e:
            # SECURITY: Fail closed on Redis errors to prevent rate limit bypass
            logger.error("Rate limit check failed - failing closed for security", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiting service temporarily unavailable. Please try again later."
            )

        # Process request
        response = await call_next(request)

        return response

    def _check_rate_limit(self, api_key: str) -> None:
        """
        Check if request is within rate limits

        Args:
            api_key: The API key to check

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        current_time = int(time.time())
        key_hash = api_key[:16]  # Use first 16 chars for privacy

        # Check per-minute limit
        minute_key = f"ratelimit:{key_hash}:minute:{current_time // 60}"
        minute_count = self._increment_counter(
            minute_key,
            ttl=60,
            limit=settings.RATE_LIMIT_PER_MINUTE
        )

        if minute_count > settings.RATE_LIMIT_PER_MINUTE:
            logger.warning(
                "Rate limit exceeded (per minute)",
                key_prefix=key_hash,
                count=minute_count,
                limit=settings.RATE_LIMIT_PER_MINUTE
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {settings.RATE_LIMIT_PER_MINUTE} requests per minute",
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": str(max(0, settings.RATE_LIMIT_PER_MINUTE - minute_count)),
                    "X-RateLimit-Reset": str((current_time // 60 + 1) * 60),
                }
            )

        # Check per-hour limit
        hour_key = f"ratelimit:{key_hash}:hour:{current_time // 3600}"
        hour_count = self._increment_counter(
            hour_key,
            ttl=3600,
            limit=settings.RATE_LIMIT_PER_HOUR
        )

        if hour_count > settings.RATE_LIMIT_PER_HOUR:
            logger.warning(
                "Rate limit exceeded (per hour)",
                key_prefix=key_hash,
                count=hour_count,
                limit=settings.RATE_LIMIT_PER_HOUR
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {settings.RATE_LIMIT_PER_HOUR} requests per hour",
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_HOUR),
                    "X-RateLimit-Remaining": str(max(0, settings.RATE_LIMIT_PER_HOUR - hour_count)),
                    "X-RateLimit-Reset": str((current_time // 3600 + 1) * 3600),
                }
            )

    def _increment_counter(self, key: str, ttl: int, limit: int) -> int:
        """
        Increment a Redis counter with TTL

        Args:
            key: Redis key
            ttl: Time to live in seconds
            limit: Rate limit (for logging)

        Returns:
            int: Current count after increment

        Raises:
            Exception: Re-raises Redis exceptions to fail closed
        """
        if not self.redis_available or self.redis_client is None:
            logger.error("Redis unavailable - cannot increment counter")
            raise Exception("Redis service unavailable")

        try:
            # Increment counter
            count = self.redis_client.incr(key)

            # Set TTL if this is the first increment
            if count == 1:
                self.redis_client.expire(key, ttl)

            return count
        except Exception as e:
            logger.error("Redis operation failed - failing closed", error=str(e), key=key)
            # Re-raise to fail closed (will trigger 503 in dispatch)
            raise


# Removed MockRedisClient - we now fail closed instead of fail open for security
