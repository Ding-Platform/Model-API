from pydantic import BaseModel


class UserContextUpdate(BaseModel):
    display_name: str | None = None
    username: str | None = None
    bio: str | None = None
    language: str | None = None
    location: str | None = None

