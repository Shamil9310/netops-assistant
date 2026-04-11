from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import Team
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_all_teams(session: AsyncSession) -> list[Team]:
    """Возвращает все команды с участниками."""
    result = await session.execute(select(Team).options(selectinload(Team.members)))
    return list(result.scalars().all())


async def get_team_by_id(session: AsyncSession, team_id: UUID) -> Team | None:
    """Возвращает команду по ID или None."""
    result = await session.execute(
        select(Team).where(Team.id == team_id).options(selectinload(Team.members))
    )
    return result.scalar_one_or_none()


async def create_team(
    session: AsyncSession,
    name: str,
    description: str | None,
    manager_id: UUID | None,
) -> Team:
    """Создаёт новую команду."""
    team = Team(name=name, description=description, manager_id=manager_id)
    session.add(team)
    await session.commit()
    await session.refresh(team)
    logger.info("Создана команда: name=%s", name)
    return team


async def update_team(
    session: AsyncSession,
    team: Team,
    name: str | None,
    description: str | None,
    manager_id: UUID | None,
) -> Team:
    """Обновляет поля команды. None-значения не изменяются."""
    if name is not None:
        team.name = name
    if description is not None:
        team.description = description
    if manager_id is not None:
        team.manager_id = manager_id
    await session.commit()
    await session.refresh(team)
    return team


async def add_member_to_team(session: AsyncSession, team: Team, user: User) -> None:
    """Добавляет пользователя в команду."""
    if user not in team.members:
        team.members.append(user)
        await session.commit()
        logger.info("Пользователь %s добавлен в команду %s", user.username, team.name)


async def remove_member_from_team(
    session: AsyncSession, team: Team, user: User
) -> None:
    """Удаляет пользователя из команды."""
    if user in team.members:
        team.members.remove(user)
        await session.commit()
        logger.info("Пользователь %s удалён из команды %s", user.username, team.name)


async def get_all_users(session: AsyncSession) -> list[User]:
    """Возвращает всех пользователей с командами."""
    result = await session.execute(select(User).options(selectinload(User.teams)))
    return list(result.scalars().all())


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    """Возвращает пользователя по ID или None."""
    result = await session.execute(
        select(User).where(User.id == user_id).options(selectinload(User.teams))
    )
    return result.scalar_one_or_none()


async def get_team_members_for_manager(
    session: AsyncSession, manager_id: UUID
) -> list[User]:
    """Возвращает всех участников команд, где текущий пользователь — менеджер.

    Менеджер видит только своих подчинённых — это ключевое ограничение видимости данных.
    """
    result = await session.execute(
        select(Team)
        .where(Team.manager_id == manager_id)
        .options(selectinload(Team.members))
    )
    teams = list(result.scalars().all())

    # Собираем уникальных участников всех команд менеджера.
    seen_ids: set[UUID] = set()
    members: list[User] = []
    for team in teams:
        for member in team.members:
            if member.id not in seen_ids:
                seen_ids.add(member.id)
                members.append(member)
    return members
