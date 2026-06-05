from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.dependencies import require_auth
from app.schemas.tts import TTSRequest
from app.services.tts import get_tts_service

settings = get_settings()

router = APIRouter(prefix="/tts", dependencies=[Depends(require_auth)])


@router.post("/stream")
async def stream_tts(
    payload: TTSRequest,
    _platform_user_id: str = Depends(require_auth),
) -> StreamingResponse:
    if not settings.TTS_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="TTS is disabled")

    tts = get_tts_service()
    if not tts.is_ready():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="TTS is not ready")

    try:
        return StreamingResponse(
            tts.stream_speech(payload.text, payload.return_visemes),
            media_type="application/x-ndjson",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TTS generation failed",
        ) from exc
