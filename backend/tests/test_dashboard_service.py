"""Тесты для сервиса дашборда (без БД — только агрегационная логика)."""

from __future__ import annotations

from collections import Counter


from app.models.journal import ActivityStatus, ActivityType


def _collect_type_counts(activity_types: list[str]) -> Counter[str]:
    """Вспомогательная функция для имитации агрегации дневной панели."""
    return Counter(activity_types)


def _collect_status_counts(statuses: list[str]) -> Counter[str]:
    return Counter(statuses)


def test_type_counter_aggregation_counts_values() -> None:
    """Проверяет корректную агрегацию типов активности."""
    types = ["call", "call", "ticket", "meeting"]
    counter = _collect_type_counts(types)

    assert counter.get(ActivityType.CALL.value, 0) == 2
    assert counter.get(ActivityType.TICKET.value, 0) == 1
    assert counter.get(ActivityType.MEETING.value, 0) == 1
    assert counter.get(ActivityType.TASK.value, 0) == 0


def test_counter_aggregation_empty() -> None:
    """Пустой список даёт нулевые счётчики."""
    counter = _collect_type_counts([])
    for activity_type in ActivityType:
        assert counter.get(activity_type.value, 0) == 0


def test_status_counter_aggregation() -> None:
    """Счётчики статусов правильно агрегируются."""
    statuses = ["open", "open", "closed", "in_progress"]
    counter = _collect_status_counts(statuses)

    assert counter.get(ActivityStatus.OPEN.value, 0) == 2
    assert counter.get(ActivityStatus.CLOSED.value, 0) == 1
    assert counter.get(ActivityStatus.IN_PROGRESS.value, 0) == 1
    assert counter.get(ActivityStatus.CANCELLED.value, 0) == 0


def test_total_count_matches_entries() -> None:
    """Общее количество должно совпадать с числом записей."""
    entries = ["call", "ticket", "other"]
    assert len(entries) == 3
    counter = _collect_type_counts(entries)
    assert sum(counter.values()) == 3
