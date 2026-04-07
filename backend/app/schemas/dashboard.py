from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.journal import ActivityEntryResponse
from app.schemas.planned_event import PlannedEventResponse


class ActivityCounters(BaseModel):
    """Счётчики активностей по типам за выбранный период."""

    total: int
    call: int
    ticket: int
    meeting: int
    task: int
    escalation: int
    other: int


class StatusCounters(BaseModel):
    """Счётчики активностей по статусам."""

    open: int
    in_progress: int
    closed: int
    cancelled: int


class TodayDashboardResponse(BaseModel):
    """Данные дашборда текущего дня.

    Агрегирует активности сотрудника за сегодня:
    счётчики, статусы, timeline записей и плановые события дня.
    """

    date: str  # ISO дата дня (YYYY-MM-DD)
    generated_at: datetime

    # Счётчики по типам и статусам — для виджетов дашборда.
    activity_counters: ActivityCounters
    status_counters: StatusCounters

    # Timeline — список всех записей журнала за день.
    timeline: list[ActivityEntryResponse]

    # Плановые события на сегодня — auto-include из planned_events.
    planned_today: list[PlannedEventResponse]
