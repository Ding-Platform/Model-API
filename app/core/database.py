from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


def get_sqlmodel_metadata():
    return SQLModel.metadata

