"""Репозиторий для работы с командами и пользователями в контексте команд."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.team import Team
from app.models.user import User
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """Репозиторий команд."""

    async def get_all(self) -> list[Team]:
        """Возвращает все команды с участниками."""
        result = await self._session.execute(
            select(Team).options(selectinload(Team.members))
        )
        return list(result.scalars().all())

    async def get_by_id(self, team_id: UUID) -> Team | None:
        """Возвращает команду по ID с участниками или None."""
        result = await self._session.execute(
            select(Team).where(Team.id == team_id).options(selectinload(Team.members))
        )
        return result.scalar_one_or_none()

    async def get_by_manager(self, manager_id: UUID) -> list[Team]:
        """Возвращает все команды, где пользователь является менеджером."""
        result = await self._session.execute(
            select(Team)
            .where(Team.manager_id == manager_id)
            .options(selectinload(Team.members))
        )
        return list(result.scalars().all())

    async def save(self, team: Team) -> Team:
        """Сохраняет новую команду и возвращает её обновлённое состояние."""
        self._session.add(team)
        await self._session.commit()
        await self._session.refresh(team)
        return team

    async def update(self, team: Team) -> Team:
        """Коммитит изменения команды."""
        await self._session.commit()
        await self._session.refresh(team)
        return team

    async def get_all_users(self) -> list[User]:
        """Возвращает всех пользователей с командами."""
        result = await self._session.execute(
            select(User).options(selectinload(User.teams))
        )
        return list(result.scalars().all())

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Возвращает пользователя по ID с командами или None."""
        result = await self._session.execute(
            select(User).where(User.id == user_id).options(selectinload(User.teams))
        )
        return result.scalar_one_or_none()
