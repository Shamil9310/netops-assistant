from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.models.user import User
from app.repositories.team import TeamRepository

logger = logging.getLogger(__name__)


async def get_all_teams(session: AsyncSession) -> list[Team]:
    """Возвращает все команды с участниками."""
    return await TeamRepository(session).get_all()


async def get_team_by_id(session: AsyncSession, team_id: UUID) -> Team | None:
    """Возвращает команду по ID или None."""
    return await TeamRepository(session).get_by_id(team_id)


async def create_team(
    session: AsyncSession,
    name: str,
    description: str | None,
    manager_id: UUID | None,
) -> Team:
    """Создаёт новую команду."""
    team = Team(name=name, description=description, manager_id=manager_id)
    result = await TeamRepository(session).save(team)
    logger.info("Создана команда: name=%s", name)
    return result


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
    return await TeamRepository(session).update(team)


async def add_member_to_team(session: AsyncSession, team: Team, user: User) -> None:
    """Добавляет пользователя в команду."""
    if user not in team.members:
        team.members.append(user)
        await TeamRepository(session).update(team)
        logger.info("Пользователь %s добавлен в команду %s", user.username, team.name)


async def remove_member_from_team(
    session: AsyncSession, team: Team, user: User
) -> None:
    """Удаляет пользователя из команды."""
    if user in team.members:
        team.members.remove(user)
        await TeamRepository(session).update(team)
        logger.info("Пользователь %s удалён из команды %s", user.username, team.name)


async def get_all_users(session: AsyncSession) -> list[User]:
    """Возвращает всех пользователей с командами."""
    return await TeamRepository(session).get_all_users()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    """Возвращает пользователя по ID или None."""
    return await TeamRepository(session).get_user_by_id(user_id)


async def get_team_members_for_manager(
    session: AsyncSession, manager_id: UUID
) -> list[User]:
    """Возвращает всех участников команд, где текущий пользователь — менеджер.

    Менеджер видит только своих подчинённых — это ключевое ограничение видимости данных.
    """
    teams = await TeamRepository(session).get_by_manager(manager_id)

    # Собираем уникальных участников всех команд менеджера.
    seen_ids: set[UUID] = set()
    members: list[User] = []
    for team in teams:
        for member in team.members:
            if member.id not in seen_ids:
                seen_ids.add(member.id)
                members.append(member)
    return members
