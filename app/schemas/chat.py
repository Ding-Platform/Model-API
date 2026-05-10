from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.chat import MessageRole
from app.schemas.user import UserContextUpdate


class CreateSessionRequest(BaseModel):
    title: str | None = None


class SendMessageRequest(BaseModel):
    message: str
    user_context: dict | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    response_time_ms: int | None = None
    created_at: datetime


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    archived: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class SessionDetailResponse(SessionResponse):
    messages: list[MessageResponse]


class ChatResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    session_id: UUID


class PaginatedSessions(BaseModel):
    items: list[SessionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class PaginatedMessages(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    page_size: int
    has_next: bool

