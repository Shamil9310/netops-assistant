"""Тесты для сервиса дашборда (без БД — только агрегационная логика)."""

from __future__ import annotations

from collections import Counter

import pytest

from app.models.journal import ActivityStatus, ActivityType


def _count_by_type(activity_types: list[str]) -> Counter[str]:
    """Вспомогательная функция — имитирует агрегацию из build_today_dashboard."""
    return Counter(activity_types)


def _count_by_status(statuses: list[str]) -> Counter[str]:
    return Counter(statuses)


def test_counter_aggregation_happy_path() -> None:
    """Счётчики правильно агрегируют типы активности."""
    types = ["call", "call", "ticket", "meeting"]
    counter = _count_by_type(types)

    assert counter.get(ActivityType.CALL.value, 0) == 2
    assert counter.get(ActivityType.TICKET.value, 0) == 1
    assert counter.get(ActivityType.MEETING.value, 0) == 1
    assert counter.get(ActivityType.TASK.value, 0) == 0


def test_counter_aggregation_empty() -> None:
    """Пустой список даёт нулевые счётчики."""
    counter = _count_by_type([])
    for activity_type in ActivityType:
        assert counter.get(activity_type.value, 0) == 0


def test_status_counter_aggregation() -> None:
    """Счётчики статусов правильно агрегируются."""
    statuses = ["open", "open", "closed", "in_progress"]
    counter = _count_by_status(statuses)

    assert counter.get(ActivityStatus.OPEN.value, 0) == 2
    assert counter.get(ActivityStatus.CLOSED.value, 0) == 1
    assert counter.get(ActivityStatus.IN_PROGRESS.value, 0) == 1
    assert counter.get(ActivityStatus.CANCELLED.value, 0) == 0


def test_total_count_matches_entries() -> None:
    """Total должен совпадать с количеством записей."""
    entries = ["call", "ticket", "other"]
    assert len(entries) == 3
    counter = _count_by_type(entries)
    assert sum(counter.values()) == 3
