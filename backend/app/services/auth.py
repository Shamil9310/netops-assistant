from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from pwdlib import PasswordHash
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user import User
from app.models.user_session import UserSession

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def hash_session_token(token: str) -> str:
    return sha256(f"{settings.secret_key}:{token}".encode()).hexdigest()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(session, username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_session(session: AsyncSession, user: User) -> str:
    raw_token = token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours)
    db_session = UserSession(user_id=user.id, token_hash=hash_session_token(raw_token), expires_at=expires_at)
    session.add(db_session)
    await session.commit()
    return raw_token


async def revoke_session(session: AsyncSession, raw_token: str) -> None:
    db_session = await get_active_session(session, raw_token)
    if db_session is None:
        return
    db_session.revoked_at = datetime.now(UTC)
    await session.commit()


async def get_active_session(session: AsyncSession, raw_token: str) -> UserSession | None:
    now = datetime.now(UTC)
    statement: Select[tuple[UserSession]] = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(UserSession.token_hash == hash_session_token(raw_token))
        .where(UserSession.revoked_at.is_(None))
        .where(UserSession.expires_at > now)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_current_user(session: AsyncSession, raw_token: str | None) -> User | None:
    if not raw_token:
        return None
    db_session = await get_active_session(session, raw_token)
    if db_session is None or db_session.user is None or not db_session.user.is_active:
        return None
    return db_session.user


async def ensure_bootstrap_user(session: AsyncSession) -> None:
    existing_user = await get_user_by_username(session, settings.bootstrap_username)
    if existing_user is not None:
        return

    session.add(
        User(
            username=settings.bootstrap_username,
            full_name=settings.bootstrap_full_name,
            password_hash=hash_password(settings.bootstrap_password),
            is_active=True,
        )
    )
    await session.commit()
