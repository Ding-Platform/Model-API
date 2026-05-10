from fastapi import APIRouter

from app.services.ollama import get_ollama_service

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    ollama_ok = await get_ollama_service().health_check()
    return {"status": "ok", "ollama_ok": ollama_ok}

