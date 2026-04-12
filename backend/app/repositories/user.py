"""Репозиторий для работы с пользователями и сессиями.

Содержит SQL-запросы к таблицам User и UserSession.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User, UserSession
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Репозиторий пользователей."""

    async def get_by_username(self, username: str) -> User | None:
        """Возвращает пользователя по имени или None если не найден."""
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Возвращает пользователя по ID с загрузкой его команд."""
        result = await self._session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.teams))
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[User]:
        """Возвращает всех пользователей с командами."""
        result = await self._session.execute(
            select(User).options(selectinload(User.teams))
        )
        return list(result.scalars().all())

    async def save(self, user: User) -> User:
        """Сохраняет нового пользователя и возвращает его обновлённое состояние."""
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Коммитит изменения пользователя."""
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Удаляет пользователя из БД."""
        await self._session.delete(user)
        await self._session.commit()


class UserSessionRepository(BaseRepository[UserSession]):
    """Репозиторий сессий пользователей."""

    async def get_active_by_token_hash(
        self,
        token_hash: str,
        now: datetime,
    ) -> UserSession | None:
        """Возвращает активную (не истёкшую, не отозванную) сессию по хэшу токена."""
        result = await self._session.execute(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(UserSession.token_hash == token_hash)
            .where(UserSession.revoked_at.is_(None))
            .where(UserSession.expires_at > now)
        )
        return result.scalar_one_or_none()

    async def save(self, session: UserSession) -> None:
        """Сохраняет новую сессию."""
        self._session.add(session)
        await self._session.commit()

    async def update(self, session: UserSession) -> None:
        """Коммитит изменения сессии (например, revoked_at)."""
        await self._session.commit()
