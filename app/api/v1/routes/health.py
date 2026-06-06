import asyncio
import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.database import engine
from app.core.redis_client import get_redis
from app.services.ollama import get_ollama_service
from app.services.tts import get_tts_service

logger = logging.getLogger(__name__)

router = APIRouter()

_HEALTH_TIMEOUT = 3.0


async def _check_db() -> bool:
    try:
        async with asyncio.timeout(_HEALTH_TIMEOUT):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.debug("Database health check failed", exc_info=True)
        return False


async def _check_redis() -> bool:
    try:
        async with asyncio.timeout(_HEALTH_TIMEOUT):
            redis = await get_redis()
            return await redis.ping()
    except Exception:
        logger.debug("Redis health check failed", exc_info=True)
        return False


async def _check_ollama() -> bool:
    try:
        async with asyncio.timeout(_HEALTH_TIMEOUT):
            return await get_ollama_service().health_check()
    except Exception:
        logger.debug("Ollama health check failed", exc_info=True)
        return False


@router.get("/health")
async def health(response: Response) -> dict:
    db_ok, redis_ok, ollama_ok = await asyncio.gather(
        _check_db(),
        _check_redis(),
        _check_ollama(),
    )
    tts_ok = get_tts_service().is_ready()
    core_ok = db_ok and redis_ok
    status_value = "ok" if core_ok and ollama_ok else "degraded"
    if not core_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": status_value,
        "db_ok": db_ok,
        "redis_ok": redis_ok,
        "ollama_ok": ollama_ok,
        "tts_ok": tts_ok,
    }
