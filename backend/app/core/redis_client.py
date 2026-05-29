"""
Shared async Redis connection pool.

Import get_redis() wherever you need Redis instead of calling
aioredis.from_url() directly. The pool is created once and reused
across all requests, so we don't pay connection-setup cost per request
and don't exhaust Redis's connection limit under load.

Usage
-----
    from app.core.redis_client import get_redis

    redis = get_redis()
    await redis.publish("channel", "message")

For pub/sub, create a pubsub object from the pool and close ONLY
the pubsub (not the whole client) when done:

    pubsub = redis.pubsub()
    await pubsub.subscribe("channel")
    ...
    await pubsub.unsubscribe("channel")
    await pubsub.aclose()
"""
import redis.asyncio as aioredis

from app.core.config import settings

_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client (lazy-initialised on first call)."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _pool