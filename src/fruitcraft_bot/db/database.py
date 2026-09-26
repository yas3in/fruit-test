"""Async SQLAlchemy database engine and session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.fruitcraft_bot.core.config import settings
from src.fruitcraft_bot.db.models import Base

# Clean architecture: uses SQLite via aiosqlite by default, but completely compatible with PostgreSQL (e.g. postgresql+asyncpg://...)
engine = create_async_engine(
    settings.db_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.db_url else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async DB session in FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
