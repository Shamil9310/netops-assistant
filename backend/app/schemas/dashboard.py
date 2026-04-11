from __future__ import annotations

from datetime import date, datetime

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
    """Данные панели за текущий день.

    Агрегирует активности сотрудника за сегодня:
    счётчики, статусы, ленту записей и плановые события дня.
    """

    date: str  # ISO дата дня (YYYY-MM-DD)
    generated_at: datetime

    # Счётчики по типам и статусам для карточек на экране.
    activity_counters: ActivityCounters
    status_counters: StatusCounters

    # Лента всех записей журнала за день.
    timeline: list[ActivityEntryResponse]

    # Плановые события на сегодня, которые подтягиваются из отдельного сервиса событий.
    planned_today: list[PlannedEventResponse]


class DashboardDatePoint(BaseModel):
    """Сводка по одному дню для исторического графика."""

    date: date
    total: int


class DashboardWeekPoint(BaseModel):
    """Сводка по одной неделе для исторического графика."""

    week_start: date
    week_end: date
    total: int


class DashboardServicePoint(BaseModel):
    """Сводка по одной услуге для диаграммы распределения."""

    service: str
    total: int
    share: float


class DashboardAnalyticsResponse(BaseModel):
    """Сводка для отдельного аналитического дашборда."""

    generated_at: datetime
    period_start: date
    period_end: date
    today_total: int
    week_total: int
    total_entries: int
    daily_series: list[DashboardDatePoint]
    weekly_series: list[DashboardWeekPoint]
    service_breakdown: list[DashboardServicePoint]
