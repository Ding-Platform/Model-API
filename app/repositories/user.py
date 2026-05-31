from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.chat import UserProfile
from app.schemas.user import UserContextUpdate


class UserRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_platform_id(self, platform_user_id: str) -> UserProfile | None:
        result = await self._db.execute(
            select(UserProfile).where(UserProfile.platform_user_id == platform_user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, platform_user_id: str) -> tuple[UserProfile, bool]:
        existing = await self.get_by_platform_id(platform_user_id)
        if existing:
            return existing, False

        profile = UserProfile(platform_user_id=platform_user_id)
        self._db.add(profile)
        await self._db.commit()
        await self._db.refresh(profile)
        return profile, True

    async def update_context(self, platform_user_id: str, data: UserContextUpdate) -> UserProfile:
        profile, _ = await self.get_or_create(platform_user_id)
        patch = data.model_dump(exclude_unset=True)
        for k, v in patch.items():
            setattr(profile, k, v)
        profile.updated_at = datetime.utcnow()
        self._db.add(profile)
        await self._db.commit()
        await self._db.refresh(profile)
        return profile

