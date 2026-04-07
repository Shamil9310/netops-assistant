from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.journal import ActivityEntry
from app.models.team import Team
from app.models.user import User


@dataclass(slots=True)
class TeamMemberWeeklySummary:
    """Агрегированная статистика сотрудника за неделю для руководителя."""

    user_id: UUID
    username: str
    full_name: str
    total_entries: int
    by_status: dict[str, int]
    by_activity_type: dict[str, int]


def _week_boundaries(week_start: date) -> tuple[datetime, datetime]:
    """Возвращает UTC-границы недельного периода от понедельника до воскресенья."""
    period_start = datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0, tzinfo=UTC)
    period_end = period_start + timedelta(days=7) - timedelta(microseconds=1)
    return period_start, period_end


def build_weekly_team_summary(
    members: list[User],
    entries: list[ActivityEntry],
) -> list[TeamMemberWeeklySummary]:
    """Собирает недельную сводку по сотрудникам команды.

    Функция выделена отдельно от доступа к БД, чтобы:
    1) упростить unit-тестирование бизнес-агрегации;
    2) не смешивать SQL и правила отображения итоговой статистики.
    """
    member_by_id = {member.id: member for member in members}
    grouped_entries: dict[UUID, list[ActivityEntry]] = {member.id: [] for member in members}

    for entry in entries:
        if entry.user_id in grouped_entries:
            grouped_entries[entry.user_id].append(entry)

    summaries: list[TeamMemberWeeklySummary] = []
    for member in members:
        member_entries = grouped_entries[member.id]
        by_status = Counter(item.status for item in member_entries)
        by_activity_type = Counter(item.activity_type for item in member_entries)

        summaries.append(
            TeamMemberWeeklySummary(
                user_id=member.id,
                username=member_by_id[member.id].username,
                full_name=member_by_id[member.id].full_name,
                total_entries=len(member_entries),
                by_status=dict(by_status),
                by_activity_type=dict(by_activity_type),
            )
        )
    return summaries


async def get_manager_members(session: AsyncSession, manager_id: UUID) -> list[User]:
    """Возвращает уникальных сотрудников всех команд, где пользователь — руководитель."""
    result = await session.execute(
        select(Team).where(Team.manager_id == manager_id).options(selectinload(Team.members))
    )
    teams = list(result.scalars().all())

    unique_members: dict[UUID, User] = {}
    for team in teams:
        for member in team.members:
            unique_members[member.id] = member
    return list(unique_members.values())


async def is_user_in_manager_scope(session: AsyncSession, manager_id: UUID, user_id: UUID) -> bool:
    """Проверяет, что сотрудник действительно относится к контуру руководителя."""
    members = await get_manager_members(session, manager_id)
    return any(member.id == user_id for member in members)


async def get_weekly_team_summary(
    session: AsyncSession,
    manager_id: UUID,
    week_start: date,
) -> list[TeamMemberWeeklySummary]:
    """Формирует недельную сводку команды по активностям журнала."""
    members = await get_manager_members(session, manager_id)
    if not members:
        return []

    member_ids = [member.id for member in members]
    period_start, period_end = _week_boundaries(week_start)

    result = await session.execute(
        select(ActivityEntry)
        .where(ActivityEntry.user_id.in_(member_ids))
        .where(ActivityEntry.created_at >= period_start)
        .where(ActivityEntry.created_at <= period_end)
    )
    entries = list(result.scalars().all())
    return build_weekly_team_summary(members, entries)
