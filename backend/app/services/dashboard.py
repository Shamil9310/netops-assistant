from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import ActivityEntry, ActivityStatus, ActivityType
from app.models.planned_event import PlannedEvent
from app.schemas.dashboard import (
    DashboardAnalyticsResponse,
    DashboardDatePoint,
    DashboardServicePoint,
    DashboardWeekPoint,
    ActivityCounters,
    StatusCounters,
    TodayDashboardResponse,
)
from app.schemas.journal import ActivityEntryResponse
from app.schemas.planned_event import PlannedEventResponse
from app.services.journal import list_entries_for_date
from app.services.planned_event import list_events_for_date


def _to_entry_response(entry: ActivityEntry) -> ActivityEntryResponse:
    """Преобразует запись журнала в схему для дашборда."""
    return ActivityEntryResponse(
        id=str(entry.id),
        user_id=str(entry.user_id),
        work_date=entry.work_date,
        activity_type=entry.activity_type,  # type: ignore[arg-type]
        status=entry.status,  # type: ignore[arg-type]
        title=entry.title,
        description=entry.description,
        resolution=entry.resolution,
        contact=entry.contact,
        service=entry.service,
        ticket_number=entry.ticket_number or entry.external_ref,
        task_url=entry.task_url,
        started_at=(
            entry.started_at.timetz().replace(tzinfo=None) if entry.started_at else None
        ),
        ended_at=(
            entry.finished_at.timetz().replace(tzinfo=None)
            if entry.finished_at
            else None
        ),
        ended_date=(entry.finished_at.date() if entry.finished_at else None),
        is_backdated=entry.created_at.date() > entry.work_date,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _to_planned_response(event: PlannedEvent) -> PlannedEventResponse:
    """Преобразует плановое событие в схему для дашборда."""
    return PlannedEventResponse(
        id=str(event.id),
        user_id=str(event.user_id),
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        external_ref=event.external_ref,
        scheduled_at=event.scheduled_at,
        is_completed=event.is_completed,
        linked_journal_entry_id=(
            str(event.linked_journal_entry_id)
            if event.linked_journal_entry_id
            else None
        ),
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _start_of_week(value: date) -> date:
    """Возвращает понедельник недели для переданной даты."""
    return value - timedelta(days=value.weekday())


def _is_tickets_entry(entry: ActivityEntry) -> bool:
    """Определяет, относится ли запись к заявкам/тикетам для аналитики."""
    return bool((entry.ticket_number or entry.external_ref or "").strip())


def _service_label(entry: ActivityEntry) -> str:
    """Возвращает читаемое имя услуги для отчётной панели."""
    if entry.service and entry.service.strip():
        return entry.service.strip()
    return "Без услуги"


async def build_today_dashboard(
    session: AsyncSession, user_id: UUID
) -> TodayDashboardResponse:
    """Строит данные дашборда текущего дня для пользователя.

    День определяется как UTC [00:00:00, 23:59:59] текущей даты.
    Агрегируем счётчики по типам и статусам из реального журнала.
    Добавляем плановые события на сегодня (auto-include).
    """
    now = datetime.now(UTC)
    return await build_day_dashboard(session, user_id, now.date())


async def build_day_dashboard(
    session: AsyncSession,
    user_id: UUID,
    work_date: date,
) -> TodayDashboardResponse:
    """Строит дашборд за выбранную рабочую дату."""
    day_start = datetime(
        work_date.year, work_date.month, work_date.day, 0, 0, 0, tzinfo=UTC
    )
    day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)

    entries = await list_entries_for_date(session, user_id, day_start, day_end)
    planned = await list_events_for_date(session, user_id, work_date)

    type_counter: Counter[str] = Counter(e.activity_type for e in entries)
    status_counter: Counter[str] = Counter(e.status for e in entries)

    return TodayDashboardResponse(
        date=work_date.isoformat(),
        generated_at=datetime.now(UTC),
        activity_counters=ActivityCounters(
            total=len(entries),
            call=type_counter.get(ActivityType.CALL.value, 0),
            ticket=type_counter.get(ActivityType.TICKET.value, 0),
            meeting=type_counter.get(ActivityType.MEETING.value, 0),
            task=type_counter.get(ActivityType.TASK.value, 0),
            escalation=type_counter.get(ActivityType.ESCALATION.value, 0),
            other=type_counter.get(ActivityType.OTHER.value, 0),
        ),
        status_counters=StatusCounters(
            open=status_counter.get(ActivityStatus.OPEN.value, 0),
            in_progress=status_counter.get(ActivityStatus.IN_PROGRESS.value, 0),
            closed=status_counter.get(ActivityStatus.CLOSED.value, 0),
            cancelled=status_counter.get(ActivityStatus.CANCELLED.value, 0),
        ),
        timeline=[_to_entry_response(e) for e in entries],
        planned_today=[_to_planned_response(e) for e in planned],
    )


async def build_analytics_dashboard(
    session: AsyncSession,
    user_id: UUID,
) -> DashboardAnalyticsResponse:
    """Строит аналитический дашборд по журналу за исторический период."""
    today = datetime.now(UTC).date()
    daily_period_start = today - timedelta(days=29)
    current_week_start = _start_of_week(today)
    weekly_period_start = current_week_start - timedelta(days=7 * 11)
    analysis_period_start = min(daily_period_start, weekly_period_start)

    result = await session.execute(
        select(ActivityEntry)
        .where(ActivityEntry.user_id == user_id)
        .where(ActivityEntry.work_date >= analysis_period_start)
        .where(ActivityEntry.work_date <= today)
        .order_by(ActivityEntry.work_date.asc(), ActivityEntry.created_at.asc())
    )
    entries = list(result.scalars().all())

    daily_counter: Counter[date] = Counter()
    weekly_counter: Counter[date] = Counter()
    service_counter: Counter[str] = Counter()

    for entry in entries:
        if not _is_tickets_entry(entry):
            continue
        weekly_counter[_start_of_week(entry.work_date)] += 1
        if entry.work_date < daily_period_start:
            continue
        daily_counter[entry.work_date] += 1
        service_counter[_service_label(entry)] += 1

    daily_series = [
        DashboardDatePoint(date=day, total=daily_counter.get(day, 0))
        for day in (daily_period_start + timedelta(days=offset) for offset in range(30))
    ]

    weekly_series = [
        DashboardWeekPoint(
            week_start=week_start,
            week_end=week_start + timedelta(days=6),
            total=weekly_counter.get(week_start, 0),
        )
        for week_start in (
            weekly_period_start + timedelta(days=7 * offset) for offset in range(12)
        )
    ]

    ordered_services = service_counter.most_common()
    total_entries = sum(daily_counter.values())
    service_breakdown = [
        DashboardServicePoint(
            service=service,
            total=total,
            share=(total / total_entries) if total_entries else 0.0,
        )
        for service, total in ordered_services
    ]

    week_total = sum(
        daily_counter.get(current_week_start + timedelta(days=offset), 0)
        for offset in range((today - current_week_start).days + 1)
    )

    return DashboardAnalyticsResponse(
        generated_at=datetime.now(UTC),
        period_start=daily_period_start,
        period_end=today,
        today_total=daily_counter.get(today, 0),
        week_total=week_total,
        total_entries=total_entries,
        daily_series=daily_series,
        weekly_series=weekly_series,
        service_breakdown=service_breakdown,
    )
