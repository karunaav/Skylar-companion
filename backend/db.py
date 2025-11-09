import os
import uuid
from typing import Optional
from datetime import datetime 

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, DateTime, func, select

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()
engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_external_id: Mapped[str] = mapped_column(String(128), index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    companion_name: Mapped[str] = mapped_column(String(120))
    preferred_style: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(  # ✅ fixed typing
        DateTime(timezone=True),
        server_default=func.now(),
    )



async def init_db_if_configured():
    """Create tables if DATABASE_URL is set. Safe to call on startup."""
    if engine is None:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Yield an async session. Only used when DATABASE_URL is configured."""
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured; persistent profiles disabled.")
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_profile(user_external_id: str) -> Optional[UserProfile]:
    if AsyncSessionLocal is None:
        return None
    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(UserProfile).where(UserProfile.user_external_id == user_external_id)
        )
        return q.scalars().first()


async def upsert_user_profile(
    user_external_id: str,
    display_name: str,
    companion_name: str,
    preferred_style: str,
) -> None:
    if AsyncSessionLocal is None:
        return
    async with AsyncSessionLocal() as session:
        q = await session.execute(
            select(UserProfile).where(UserProfile.user_external_id == user_external_id)
        )
        profile = q.scalars().first()
        if profile:
            profile.display_name = display_name
            profile.companion_name = companion_name
            profile.preferred_style = preferred_style
        else:
            profile = UserProfile(
                user_external_id=user_external_id,
                display_name=display_name,
                companion_name=companion_name,
                preferred_style=preferred_style,
            )
            session.add(profile)
        await session.commit()
