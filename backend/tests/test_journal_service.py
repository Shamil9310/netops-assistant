"""Тесты для сервисного слоя журнала (без БД — только бизнес-логика)."""

from __future__ import annotations

import pytest

from app.models.journal import ActivityStatus, ActivityType


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
