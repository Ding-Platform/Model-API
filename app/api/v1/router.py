from fastapi import APIRouter

from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.tts import router as tts_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router, tags=["health"])
router.include_router(chat_router, tags=["chat"])
router.include_router(tts_router, tags=["tts"])

