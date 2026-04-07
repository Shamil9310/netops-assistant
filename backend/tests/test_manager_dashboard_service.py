"""Тесты сервиса manager dashboard: недельная сводка команды."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.services import manager_dashboard as manager_dashboard_service


@dataclass(slots=True)
class _FakeUser:
    id: object
    username: str
    full_name: str


@dataclass(slots=True)
class _FakeEntry:
    user_id: object
    status: str
    activity_type: str


def test_build_weekly_team_summary_happy_path() -> None:
    """Проверяет корректную агрегацию по сотруднику, статусам и типам активности."""
    user_a_id = uuid4()
    user_b_id = uuid4()
    members = [
        _FakeUser(id=user_a_id, username="anna", full_name="Анна Смирнова"),
        _FakeUser(id=user_b_id, username="ivan", full_name="Иван Кузнецов"),
    ]
    entries = [
        _FakeEntry(user_id=user_a_id, status="closed", activity_type="ticket"),
        _FakeEntry(user_id=user_a_id, status="open", activity_type="call"),
        _FakeEntry(user_id=user_a_id, status="closed", activity_type="ticket"),
        _FakeEntry(user_id=user_b_id, status="in_progress", activity_type="task"),
    ]

    summary = manager_dashboard_service.build_weekly_team_summary(members, entries)  # type: ignore[arg-type]

    assert len(summary) == 2
    anna = next(item for item in summary if item.username == "anna")
    ivan = next(item for item in summary if item.username == "ivan")

    assert anna.total_entries == 3
    assert anna.by_status["closed"] == 2
    assert anna.by_status["open"] == 1
    assert anna.by_activity_type["ticket"] == 2
    assert anna.by_activity_type["call"] == 1

    assert ivan.total_entries == 1
    assert ivan.by_status["in_progress"] == 1
    assert ivan.by_activity_type["task"] == 1


def test_build_weekly_team_summary_empty_members() -> None:
    """Edge-case: если сотрудников нет, сводка должна быть пустой."""
    summary = manager_dashboard_service.build_weekly_team_summary([], [])  # type: ignore[arg-type]
    assert summary == []


def test_build_weekly_team_summary_ignores_foreign_entries() -> None:
    """Проверяет, что активности чужих сотрудников не попадают в сводку команды."""
    user_id = uuid4()
    foreign_id = uuid4()
    members = [_FakeUser(id=user_id, username="maria", full_name="Мария Орлова")]
    entries = [
        _FakeEntry(user_id=foreign_id, status="closed", activity_type="ticket"),
        _FakeEntry(user_id=user_id, status="closed", activity_type="task"),
    ]

    summary = manager_dashboard_service.build_weekly_team_summary(members, entries)  # type: ignore[arg-type]

    assert len(summary) == 1
    assert summary[0].total_entries == 1
    assert summary[0].by_activity_type == {"task": 1}
