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


def test_create_request_rejects_invalid_time_range() -> None:
    """Время окончания не может быть раньше времени начала."""
    with pytest.raises(ValueError, match="окончания"):
        ActivityEntryCreateRequest(
            work_date=date(2026, 4, 7),
            activity_type="task",
            status="open",
            title="Некорректный интервал",
            started_at=time(11, 0),
            ended_at=time(10, 0),
        )


def test_update_request_rejects_invalid_time_range() -> None:
    """Та же проверка должна работать и для partial update."""
    with pytest.raises(ValueError, match="окончания"):
        ActivityEntryUpdateRequest(
            started_at=time(18, 0),
            ended_at=time(17, 59),
        )
