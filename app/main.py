import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.redis_client import close_redis
from app.services.ollama import get_ollama_service
from app.services.tts import get_tts_service

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def _load_tts_background() -> None:
    try:
        await asyncio.to_thread(get_tts_service().load)
    except Exception:
        logger.exception("Background TTS load failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting %s v%s (%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    tts_task: asyncio.Task | None = None
    if settings.TTS_ENABLED:
        tts_task = asyncio.create_task(_load_tts_background())
    yield
    if tts_task is not None and not tts_task.done():
        tts_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await tts_task
    await close_redis()
    await get_ollama_service().close()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug("→ %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.debug("← %s %s %d", request.method, request.url.path, response.status_code)
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again."},
        )

    app.include_router(v1_router)
    return app


app = create_app()

