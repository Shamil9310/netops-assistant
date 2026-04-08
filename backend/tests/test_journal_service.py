"""Тесты для сервисного слоя журнала (без БД — только бизнес-логика)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.journal import ActivityStatus, ActivityType
from app.schemas.journal import ActivityEntryCreateRequest
from app.services.journal import create_activity_entry


# ---------------------------------------------------------------------------
# ActivityType
# ---------------------------------------------------------------------------


def test_activity_type_values_are_stable() -> None:
    """Значения типов активности не должны меняться — хранятся в БД."""
    assert ActivityType.CALL.value == "call"
    assert ActivityType.TICKET.value == "ticket"
    assert ActivityType.MEETING.value == "meeting"
    assert ActivityType.TASK.value == "task"
    assert ActivityType.ESCALATION.value == "escalation"
    assert ActivityType.OTHER.value == "other"


def test_all_activity_types_are_unique() -> None:
    """Все типы активности должны иметь уникальные строковые значения."""
    values = [t.value for t in ActivityType]
    assert len(values) == len(set(values))


def test_activity_type_count() -> None:
    """Количество типов активности должно соответствовать ожиданиям."""
    assert len(list(ActivityType)) == 6


# ---------------------------------------------------------------------------
# ActivityStatus
# ---------------------------------------------------------------------------


def test_activity_status_values_are_stable() -> None:
    """Значения статусов не должны меняться — хранятся в БД."""
    assert ActivityStatus.OPEN.value == "open"
    assert ActivityStatus.IN_PROGRESS.value == "in_progress"
    assert ActivityStatus.CLOSED.value == "closed"
    assert ActivityStatus.CANCELLED.value == "cancelled"


def test_all_statuses_are_unique() -> None:
    """Все статусы должны иметь уникальные строковые значения."""
    values = [s.value for s in ActivityStatus]
    assert len(values) == len(set(values))


def test_activity_status_count() -> None:
    """Количество статусов должно соответствовать ожиданиям."""
    assert len(list(ActivityStatus)) == 4


def test_invalid_activity_type_not_in_enum() -> None:
    """Некорректный тип активности не входит в перечисление."""
    valid_types = {t.value for t in ActivityType}
    assert "phone" not in valid_types
    assert "email" not in valid_types
    assert "" not in valid_types


def test_invalid_status_not_in_enum() -> None:
    """Некорректный статус не входит в перечисление."""
    valid_statuses = {s.value for s in ActivityStatus}
    assert "pending" not in valid_statuses
    assert "done" not in valid_statuses
    assert "" not in valid_statuses


@pytest.mark.asyncio
async def test_create_activity_entry_uses_previous_ended_at_as_started_at() -> None:
    """Если started_at не передан, берём ended_at предыдущей записи за ту же дату."""
    previous_finished_at = datetime(2026, 4, 7, 12, 45, tzinfo=UTC)
    execute_result = SimpleNamespace(scalar_one_or_none=lambda: previous_finished_at)

    class FakeSession:
        def __init__(self) -> None:
            self.added = None

        async def execute(self, statement):
            return execute_result

        def add(self, entry) -> None:
            self.added = entry

        async def commit(self) -> None:
            return None

        async def refresh(self, entry) -> None:
            return None

    session = FakeSession()

    payload = ActivityEntryCreateRequest(
        work_date=date(2026, 4, 7),
        activity_type="task",
        status="open",
        title="Новая задача",
        started_at=None,
        ended_at=None,
    )
    user = SimpleNamespace(id=uuid4())

    created = await create_activity_entry(session=session, user=user, payload=payload)

    assert created.started_at == datetime(2026, 4, 7, 12, 45, tzinfo=UTC)
    assert created.finished_at is None
