from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import ActivityEntry, ActivityStatus, ActivityType
from app.models.planned_event import PlannedEvent
from app.schemas.dashboard import ActivityCounters, StatusCounters, TodayDashboardResponse
from app.schemas.journal import ActivityEntryResponse
from app.schemas.planned_event import PlannedEventResponse
from app.services.journal import list_entries_for_date
from app.services.planned_event import list_events_for_date


def _to_entry_response(entry: ActivityEntry) -> ActivityEntryResponse:
    return ActivityEntryResponse(
        id=str(entry.id),
        user_id=str(entry.user_id),
        work_date=entry.work_date,
        activity_type=entry.activity_type,
        status=entry.status,
        title=entry.title,
        description=entry.description,
        ticket_number=entry.ticket_number or entry.external_ref,
        started_at=entry.started_at.timetz().replace(tzinfo=None) if entry.started_at else None,
        ended_at=entry.finished_at.timetz().replace(tzinfo=None) if entry.finished_at else None,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _to_planned_response(event: PlannedEvent) -> PlannedEventResponse:
    return PlannedEventResponse(
        id=str(event.id),
        user_id=str(event.user_id),
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        external_ref=event.external_ref,
        scheduled_at=event.scheduled_at,
        is_completed=event.is_completed,
        linked_journal_entry_id=str(event.linked_journal_entry_id) if event.linked_journal_entry_id else None,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


async def build_today_dashboard(session: AsyncSession, user_id: UUID) -> TodayDashboardResponse:
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
    day_start = datetime(work_date.year, work_date.month, work_date.day, 0, 0, 0, tzinfo=UTC)
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
