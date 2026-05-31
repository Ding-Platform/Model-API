import json

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


class RedisCache:
    async def get(self, key: str) -> str | None:
        r = await get_redis()
        return await r.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        r = await get_redis()
        if ttl is not None:
            await r.set(key, value, ex=ttl)
        else:
            await r.set(key, value)

    async def delete(self, key: str) -> None:
        r = await get_redis()
        await r.delete(key)

