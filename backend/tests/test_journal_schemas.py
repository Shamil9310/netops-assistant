"""Тесты схем журнала: валидация времени и обязательных полей."""

from __future__ import annotations

from datetime import date, time

import pytest

from app.schemas.journal import ActivityEntryCreateRequest, ActivityEntryUpdateRequest


def test_create_request_happy_path() -> None:
    """Создание валидной схемы проходит успешно."""
    payload = ActivityEntryCreateRequest(
        work_date=date(2026, 4, 7),
        activity_type="task",
        status="open",
        title="Разбор SR",
        description="Описание",
        ticket_number="SR-1",
        started_at=time(10, 0),
        ended_at=time(11, 0),
    )
    assert payload.work_date.isoformat() == "2026-04-07"


def test_create_request_allows_next_day_closure() -> None:
    payload = ActivityEntryCreateRequest(
        work_date=date(2026, 4, 7),
        activity_type="task",
        status="open",
        title="Разбор SR",
        started_at=time(12, 3),
        ended_at=time(11, 11),
        ended_date=date(2026, 4, 8),
    )
    assert payload.ended_date == date(2026, 4, 8)


def test_create_request_rejects_invalid_time_range() -> None:
    """Время окончания не может быть раньше времени начала."""
    with pytest.raises(ValueError, match="окончания"):
        ActivityEntryCreateRequest(
            work_date=date(2026, 4, 7),
            activity_type="task",
            status="open",
            title="Некорректный интервал",
            started_at=time(23, 30),
            ended_at=time(1, 15),
        )


def test_update_request_rejects_invalid_time_range() -> None:
    """Та же проверка должна работать и для partial update."""
    with pytest.raises(ValueError, match="окончания"):
        ActivityEntryUpdateRequest(
            started_at=time(18, 0),
            ended_at=time(17, 59),
        )


def test_create_request_rejects_ended_date_before_work_date() -> None:
    with pytest.raises(ValueError, match="Дата окончания"):
        ActivityEntryCreateRequest(
            work_date=date(2026, 4, 7),
            activity_type="task",
            status="open",
            title="Некорректная дата",
            ended_date=date(2026, 4, 6),
        )
