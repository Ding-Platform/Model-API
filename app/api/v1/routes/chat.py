from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.dependencies import require_auth
from app.core.redis_client import RedisCache
from app.schemas.chat import (
    ChatResponse,
    CreateSessionRequest,
    PaginatedMessages,
    PaginatedSessions,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
)
from app.schemas.user import UserContextUpdate
from app.services.chat import ChatService
from app.services.ollama import get_ollama_service

settings = get_settings()

router = APIRouter(prefix="/chat", dependencies=[Depends(require_auth)])


def _get_chat_service(db: AsyncSession) -> ChatService:
    return ChatService(db=db, ollama=get_ollama_service(), cache=RedisCache())


@router.patch("/me/context", status_code=status.HTTP_204_NO_CONTENT)
async def sync_user_context(
    payload: UserContextUpdate,
    platform_user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await _get_chat_service(db).sync_user_context(platform_user_id, payload)


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    platform_user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    return await _get_chat_service(db).create_session(platform_user_id, payload)


@router.get("/sessions", response_model=PaginatedSessions)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    platform_user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedSessions:
    return await _get_chat_service(db).list_sessions(platform_user_id, page, page_size)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    platform_user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> SessionDetailResponse:
    return await _get_chat_service(db).get_session_detail(platform_user_id, session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_session(
    session_id: str,
    platform_user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    await _get_chat_service(db).archive_session(platform_user_id, session_id)


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    payload: SendMessageRequest,
    platform_user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    return await _get_chat_service(db).send_message(platform_user_id, session_id, payload)


@router.get("/sessions/{session_id}/messages", response_model=PaginatedMessages)
async def list_messages(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    platform_user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedMessages:
    return await _get_chat_service(db).list_messages(platform_user_id, session_id, page, page_size)

