"""Тесты для сервисного слоя плановых событий (без БД)."""

from __future__ import annotations


from app.models.planned_event import PlannedEventType


def test_planned_event_type_values_are_stable() -> None:
    """Значения типов событий не должны меняться — хранятся в БД."""
    assert PlannedEventType.CALL.value == "call"
    assert PlannedEventType.MEETING.value == "meeting"
    assert PlannedEventType.MAINTENANCE.value == "maintenance"
    assert PlannedEventType.DEADLINE.value == "deadline"
    assert PlannedEventType.OTHER.value == "other"


def test_all_event_types_are_unique() -> None:
    """Все типы событий должны иметь уникальные строковые значения."""
    values = [t.value for t in PlannedEventType]
    assert len(values) == len(set(values))


def test_planned_event_type_count() -> None:
    """Количество типов плановых событий должно соответствовать ожиданиям."""
    assert len(list(PlannedEventType)) == 5


def test_invalid_event_type_not_in_enum() -> None:
    """Некорректный тип события не входит в перечисление."""
    valid_types = {t.value for t in PlannedEventType}
    assert "task" not in valid_types
    assert "ticket" not in valid_types
    assert "" not in valid_types
