"""Тесты сервиса недельной сводки по команде."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.services import manager_dashboard as manager_dashboard_service


@dataclass(slots=True)
class _TeamMemberStub:
    id: object
    username: str
    full_name: str


@dataclass(slots=True)
class _ActivityEntryStub:
    user_id: object
    status: str
    activity_type: str


def test_build_weekly_team_summary_aggregates_team_data() -> None:
    """Проверяет корректную агрегацию по сотруднику, статусам и типам активности."""
    user_a_id = uuid4()
    user_b_id = uuid4()
    members = [
        _TeamMemberStub(id=user_a_id, username="anna", full_name="Анна Смирнова"),
        _TeamMemberStub(id=user_b_id, username="ivan", full_name="Иван Кузнецов"),
    ]
    entries = [
        _ActivityEntryStub(user_id=user_a_id, status="closed", activity_type="ticket"),
        _ActivityEntryStub(user_id=user_a_id, status="open", activity_type="call"),
        _ActivityEntryStub(user_id=user_a_id, status="closed", activity_type="ticket"),
        _ActivityEntryStub(
            user_id=user_b_id, status="in_progress", activity_type="task"
        ),
    ]

    weekly_summary = manager_dashboard_service.build_weekly_team_summary(  # type: ignore[arg-type]
        members, entries
    )

    assert len(weekly_summary) == 2
    anna = next(item for item in weekly_summary if item.username == "anna")
    ivan = next(item for item in weekly_summary if item.username == "ivan")

    assert anna.total_entries == 3
    assert anna.by_status["closed"] == 2
    assert anna.by_status["open"] == 1
    assert anna.by_activity_type["ticket"] == 2
    assert anna.by_activity_type["call"] == 1

    assert ivan.total_entries == 1
    assert ivan.by_status["in_progress"] == 1
    assert ivan.by_activity_type["task"] == 1


def test_build_weekly_team_summary_empty_members() -> None:
    """Если сотрудников нет, сводка тоже должна быть пустой."""
    weekly_summary = manager_dashboard_service.build_weekly_team_summary(  # type: ignore[arg-type]
        [], []
    )
    assert weekly_summary == []


def test_build_weekly_team_summary_ignores_foreign_entries() -> None:
    """Проверяет, что активности чужих сотрудников не попадают в сводку команды."""
    user_id = uuid4()
    foreign_id = uuid4()
    members = [_TeamMemberStub(id=user_id, username="maria", full_name="Мария Орлова")]
    entries = [
        _ActivityEntryStub(user_id=foreign_id, status="closed", activity_type="ticket"),
        _ActivityEntryStub(user_id=user_id, status="closed", activity_type="task"),
    ]

    weekly_summary = manager_dashboard_service.build_weekly_team_summary(  # type: ignore[arg-type]
        members, entries
    )

    assert len(weekly_summary) == 1
    assert weekly_summary[0].total_entries == 1
    assert weekly_summary[0].by_activity_type == {"task": 1}
