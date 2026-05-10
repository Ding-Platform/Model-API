from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis_client import RedisCache
from app.models.chat import MessageRole
from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.schemas.chat import (
    ChatResponse,
    CreateSessionRequest,
    MessageResponse,
    PaginatedMessages,
    PaginatedSessions,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
)
from app.schemas.user import UserContextUpdate
from app.services.ollama import OllamaService

settings = get_settings()

_CACHE_USER_CONTEXT_KEY = "user:{platform_user_id}:context"


class ChatService:
    def __init__(self, db: AsyncSession, ollama: OllamaService, cache: RedisCache):
        self._db = db
        self._ollama = ollama
        self._cache = cache
        self._user_repo = UserRepository(db)
        self._chat_repo = ChatRepository(db)

    async def sync_user_context(self, platform_user_id: str, data: UserContextUpdate) -> None:
        await self._user_repo.update_context(platform_user_id, data)
        await self._cache.delete(_CACHE_USER_CONTEXT_KEY.format(platform_user_id=platform_user_id))

    async def _get_user_context_string(self, platform_user_id: str) -> str:
        cache_key = _CACHE_USER_CONTEXT_KEY.format(platform_user_id=platform_user_id)
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        profile, _ = await self._user_repo.get_or_create(platform_user_id)
        context_str = profile.to_ai_context()
        await self._cache.set(cache_key, context_str, ttl=settings.REDIS_CHAT_TTL)
        return context_str

    async def create_session(self, platform_user_id: str, req: CreateSessionRequest) -> SessionResponse:
        profile, _ = await self._user_repo.get_or_create(platform_user_id)
        session = await self._chat_repo.create_session(profile, title=req.title)
        return SessionResponse.model_validate({**session.__dict__, "message_count": 0})

    async def list_sessions(
        self, platform_user_id: str, page: int, page_size: int
    ) -> PaginatedSessions:
        profile = await self._user_repo.get_by_platform_id(platform_user_id)
        if not profile:
            return PaginatedSessions(items=[], total=0, page=page, page_size=page_size, has_next=False)

        sessions, total = await self._chat_repo.list_sessions(profile.id, page=page, page_size=page_size)

        items: list[SessionResponse] = []
        for s in sessions:
            _, msg_total = await self._chat_repo.list_messages(s.id, page=1, page_size=settings.MAX_PAGE_SIZE)
            items.append(SessionResponse.model_validate({**s.__dict__, "message_count": msg_total}))

        return PaginatedSessions(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
        )

    async def get_session_detail(self, platform_user_id: str, session_id: str) -> SessionDetailResponse:
        profile = await self._user_repo.get_by_platform_id(platform_user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        session = await self._chat_repo.get_session(session_id, profile.id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        messages, _ = await self._chat_repo.list_messages(session.id, page=1, page_size=settings.MAX_PAGE_SIZE)
        message_items = [MessageResponse.model_validate(m) for m in messages]
        return SessionDetailResponse.model_validate(
            {**session.__dict__, "message_count": len(message_items), "messages": message_items}
        )

    async def archive_session(self, platform_user_id: str, session_id: str) -> None:
        profile = await self._user_repo.get_by_platform_id(platform_user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        ok = await self._chat_repo.archive_session(session_id, profile.id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    async def send_message(
        self,
        platform_user_id: str,
        session_id: str,
        req: SendMessageRequest,
    ) -> ChatResponse:
        if req.user_context:
            try:
                ctx_update = UserContextUpdate.model_validate(req.user_context)
                await self.sync_user_context(platform_user_id, ctx_update)
            except Exception:
                pass

        profile, _ = await self._user_repo.get_or_create(platform_user_id)
        session = await self._chat_repo.get_session(session_id, profile.id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

        recent = await self._chat_repo.get_recent_messages(
            session_id, limit=settings.OLLAMA_MAX_CONTEXT_MESSAGES
        )
        history = [{"role": m.role.value, "content": m.content} for m in recent]

        user_context_str = await self._get_user_context_string(platform_user_id)

        ollama_resp = await self._ollama.generate(
            user_message=req.message,
            user_context=user_context_str,
            history=history,
        )

        user_msg = await self._chat_repo.add_message(
            session,
            role=MessageRole.USER,
            content=req.message,
        )
        assistant_msg = await self._chat_repo.add_message(
            session,
            role=MessageRole.ASSISTANT,
            content=ollama_resp.text,
            prompt_tokens=ollama_resp.prompt_tokens,
            completion_tokens=ollama_resp.completion_tokens,
            response_time_ms=ollama_resp.response_time_ms,
        )

        if session.title is None:
            short_title = req.message[:60].strip()
            if len(req.message) > 60:
                short_title += "…"
            await self._chat_repo.update_session_title(session, short_title)

        return ChatResponse(
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
            session_id=session.id,
        )

    async def list_messages(
        self,
        platform_user_id: str,
        session_id: str,
        page: int,
        page_size: int,
    ) -> PaginatedMessages:
        profile = await self._user_repo.get_by_platform_id(platform_user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        session = await self._chat_repo.get_session(session_id, profile.id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        messages, total = await self._chat_repo.list_messages(session.id, page, page_size)
        return PaginatedMessages(
            items=[MessageResponse.model_validate(m) for m in messages],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
        )

