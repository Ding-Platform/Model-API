import enum
import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    platform_user_id: str = Field(index=True, unique=True)

    display_name: str | None = None
    username: str | None = None
    bio: str | None = None
    language: str | None = None
    location: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    sessions: list["ChatSession"] = Relationship(back_populates="user")

    def to_ai_context(self) -> str:
        parts: list[str] = []
        if self.display_name:
            parts.append(f"Name: {self.display_name}")
        if self.username:
            parts.append(f"Username: {self.username}")
        if self.bio:
            parts.append(f"Bio: {self.bio}")
        if self.language:
            parts.append(f"Preferred language: {self.language}")
        if self.location:
            parts.append(f"Location: {self.location}")
        return "\n".join(parts).strip() or "No user profile available."


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)

    title: str | None = Field(default=None, index=True)
    archived: bool = Field(default=False, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    user: UserProfile = Relationship(back_populates="sessions")
    messages: list["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    session_id: uuid.UUID = Field(foreign_key="chat_sessions.id", index=True)

    role: MessageRole = Field(index=True)
    content: str

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    response_time_ms: int | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)

    session: ChatSession = Relationship(back_populates="messages")

