from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.chat import ChatMessage, ChatSession, MessageRole, UserProfile


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_session(self, profile: UserProfile, title: str | None) -> ChatSession:
        session = ChatSession(user_id=profile.id, title=title)
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def get_session(self, session_id: str | UUID, user_id: UUID) -> ChatSession | None:
        sid = UUID(str(session_id))
        result = await self._db.execute(
            select(ChatSession).where(
                ChatSession.id == sid, ChatSession.user_id == user_id, ChatSession.archived == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def archive_session(self, session_id: str | UUID, user_id: UUID) -> bool:
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        session.archived = True
        session.updated_at = datetime.utcnow()
        self._db.add(session)
        await self._db.commit()
        return True

    async def update_session_title(self, session: ChatSession, title: str) -> ChatSession:
        session.title = title
        session.updated_at = datetime.utcnow()
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def list_sessions(
        self, user_id: UUID, page: int, page_size: int
    ) -> tuple[list[ChatSession], int]:
        page = max(page, 1)
        page_size = max(page_size, 1)
        offset = (page - 1) * page_size

        total_result = await self._db.execute(
            select(func.count()).select_from(ChatSession).where(
                ChatSession.user_id == user_id, ChatSession.archived == False  # noqa: E712
            )
        )
        total = int(total_result.scalar_one())

        result = await self._db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.archived == False)  # noqa: E712
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def add_message(
        self,
        session: ChatSession,
        role: MessageRole,
        content: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        response_time_ms: int | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session.id,
            role=role,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            response_time_ms=response_time_ms,
        )
        self._db.add(msg)
        session.updated_at = datetime.utcnow()
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(msg)
        return msg

    async def list_messages(
        self, session_id: str | UUID, page: int, page_size: int
    ) -> tuple[list[ChatMessage], int]:
        page = max(page, 1)
        page_size = max(page_size, 1)
        offset = (page - 1) * page_size
        sid = UUID(str(session_id))

        total_result = await self._db.execute(
            select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == sid)
        )
        total = int(total_result.scalar_one())

        result = await self._db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == sid)
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_recent_messages(self, session_id: str | UUID, limit: int) -> list[ChatMessage]:
        sid = UUID(str(session_id))
        limit = max(limit, 1)
        result = await self._db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == sid)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        msgs = list(result.scalars().all())
        msgs.reverse()
        return msgs

