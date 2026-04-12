from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_timer import (
    WorkTimerInterruption,
    WorkTimerSession,
    WorkTimerSessionStatus,
    WorkTimerTask,
    WorkTimerTaskStatus,
)
from app.models.user import User
from app.repositories.work_timer import WorkTimerRepository
from app.schemas.journal import ActivityEntryCreateRequest
from app.schemas.work_timer import (
    WorkTimerDaySummary,
    WorkTimerInterruptionResponse,
    WorkTimerSessionResponse,
    WorkTimerTagSummary,
    WorkTimerTaskCreateRequest,
    WorkTimerTaskResponse,
    WorkTimerTaskSummary,
    WorkTimerTaskUpdateRequest,
    WorkTimerTimerActionRequest,
    WorkTimerWeeklySummaryResponse,
)
from app.services.journal import create_activity_entry


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_tags(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized = []
    for value in values:
        tag = value.strip()
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized


def _interruption_duration_seconds(
    interruption: WorkTimerInterruption, now: datetime | None = None
) -> int:
    finish = interruption.ended_at or now or _utc_now()
    delta = finish - interruption.started_at
    if delta.total_seconds() <= 0:
        return 0
    return int(delta.total_seconds())


def _session_interruption_seconds(
    session: WorkTimerSession, now: datetime | None = None
) -> int:
    return sum(
        _interruption_duration_seconds(interruption, now)
        for interruption in session.interruptions
    )


def _session_duration_seconds(
    session: WorkTimerSession, now: datetime | None = None
) -> int:
    finish = session.ended_at or now or _utc_now()
    delta = finish - session.started_at
    if delta.total_seconds() <= 0:
        return 0
    total = int(delta.total_seconds()) - _session_interruption_seconds(session, now)
    return max(total, 0)


def _task_total_seconds(task: WorkTimerTask, now: datetime | None = None) -> int:
    return sum(_session_duration_seconds(session, now) for session in task.sessions)


def _task_interruption_seconds(task: WorkTimerTask, now: datetime | None = None) -> int:
    return sum(_session_interruption_seconds(session, now) for session in task.sessions)


def _task_interruptions_count(task: WorkTimerTask) -> int:
    return sum(len(session.interruptions) for session in task.sessions)


def _interruption_response(
    interruption: WorkTimerInterruption, now: datetime | None = None
) -> WorkTimerInterruptionResponse:
    return WorkTimerInterruptionResponse(
        id=str(interruption.id),
        session_id=str(interruption.session_id),
        reason=interruption.reason,
        started_at=interruption.started_at,
        ended_at=interruption.ended_at,
        duration_seconds=_interruption_duration_seconds(interruption, now),
        created_at=interruption.created_at,
        updated_at=interruption.updated_at,
    )


def _session_response(
    session: WorkTimerSession, now: datetime | None = None
) -> WorkTimerSessionResponse:
    return WorkTimerSessionResponse(
        id=str(session.id),
        task_id=str(session.task_id),
        status=WorkTimerSessionStatus(session.status),
        tags_snapshot=list(session.tags_snapshot or []),
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=_session_duration_seconds(session, now),
        interruption_seconds=_session_interruption_seconds(session, now),
        interruptions_count=len(session.interruptions),
        created_at=session.created_at,
        updated_at=session.updated_at,
        interruptions=[
            _interruption_response(item, now) for item in session.interruptions
        ],
    )


def _task_response(
    task: WorkTimerTask, now: datetime | None = None
) -> WorkTimerTaskResponse:
    active_session = next(
        (session for session in task.sessions if session.ended_at is None),
        None,
    )
    return WorkTimerTaskResponse(
        id=str(task.id),
        user_id=str(task.user_id),
        title=task.title,
        description=task.description,
        task_ref=task.task_ref,
        task_url=task.task_url,
        tags=list(task.tags or []),
        order_index=task.order_index,
        status=WorkTimerTaskStatus(task.status),
        completed_at=task.completed_at,
        total_seconds=_task_total_seconds(task, now),
        interruption_seconds=_task_interruption_seconds(task, now),
        interruptions_count=_task_interruptions_count(task),
        active_session_id=str(active_session.id) if active_session else None,
        active_session_started_at=active_session.started_at if active_session else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
        sessions=[_session_response(session, now) for session in task.sessions],
    )


def _ensure_owned_task(task: WorkTimerTask, user_id: UUID) -> None:
    if task.user_id != user_id:
        raise ValueError("Задача не найдена")


def _ensure_single_active_session(
    active_session: WorkTimerSession | None,
    task: WorkTimerTask,
) -> WorkTimerSession | None:
    if active_session is None:
        return None
    if active_session.task_id == task.id:
        return active_session
    raise ValueError("Сначала останови текущий активный таймер")


class _WeeklyTaskAggregate(TypedDict):
    title: str
    seconds: int
    sessions: int
    interruptions: int
    tags: list[str]


async def list_tasks(
    session: AsyncSession, user_id: UUID
) -> list[WorkTimerTaskResponse]:
    tasks = await WorkTimerRepository(session).list_tasks(user_id)
    return [_task_response(task) for task in tasks]


async def get_task(
    session: AsyncSession, user_id: UUID, task_id: UUID
) -> WorkTimerTask | None:
    return await WorkTimerRepository(session).get_task_by_id(user_id, task_id)


async def create_task(
    session: AsyncSession,
    user: User,
    payload: WorkTimerTaskCreateRequest,
) -> WorkTimerTaskResponse:
    task = WorkTimerTask(
        user_id=user.id,
        title=payload.title.strip(),
        description=_normalize_text(payload.description),
        task_ref=_normalize_text(payload.task_ref),
        task_url=_normalize_text(payload.task_url),
        tags=_normalize_tags(payload.tags),
        order_index=payload.order_index,
        status=payload.status.value,
    )
    result = await WorkTimerRepository(session).save_task(task)
    return _task_response(result)


async def update_task(
    session: AsyncSession,
    task: WorkTimerTask,
    payload: WorkTimerTaskUpdateRequest,
) -> WorkTimerTaskResponse:
    if payload.title is not None:
        task.title = payload.title.strip()
    if "description" in payload.model_fields_set:
        task.description = _normalize_text(payload.description)
    if "task_ref" in payload.model_fields_set:
        task.task_ref = _normalize_text(payload.task_ref)
    if "task_url" in payload.model_fields_set:
        task.task_url = _normalize_text(payload.task_url)
    if payload.tags is not None:
        task.tags = _normalize_tags(payload.tags)
    if payload.order_index is not None:
        task.order_index = payload.order_index
    if payload.status is not None:
        task.status = payload.status.value
        if payload.status == WorkTimerTaskStatus.DONE and task.completed_at is None:
            task.completed_at = payload.completed_at or _utc_now()
        elif (
            payload.status != WorkTimerTaskStatus.DONE
            and payload.completed_at is not None
        ):
            task.completed_at = payload.completed_at
    if payload.completed_at is not None:
        task.completed_at = payload.completed_at
    updated = await WorkTimerRepository(session).update_task(task)
    return _task_response(updated)


async def delete_task(session: AsyncSession, task: WorkTimerTask) -> None:
    await WorkTimerRepository(session).delete_task(task)


async def change_timer(
    session: AsyncSession,
    task: WorkTimerTask,
    user: User,
    payload: WorkTimerTimerActionRequest,
    now: datetime | None = None,
) -> WorkTimerTaskResponse:
    repo = WorkTimerRepository(session)
    now = now or _utc_now()
    _ensure_owned_task(task, user.id)

    active_session = await repo.get_active_session_for_user(user.id)
    if payload.action == "start":
        if task.status in {
            WorkTimerTaskStatus.DONE.value,
            WorkTimerTaskStatus.CANCELLED.value,
        }:
            raise ValueError(
                "Нельзя запускать таймер для завершённой или отменённой задачи"
            )
        if (
            active_session
            and active_session.task_id == task.id
            and active_session.status == WorkTimerSessionStatus.PAUSED.value
        ):
            return await _resume_session(session, repo, task, active_session, now)
        if (
            active_session
            and active_session.task_id == task.id
            and active_session.status == WorkTimerSessionStatus.RUNNING.value
        ):
            fresh_task = await repo.get_task_by_id(user.id, task.id)
            return _task_response(fresh_task or task, now)
        _ensure_single_active_session(active_session, task)
        task.status = WorkTimerTaskStatus.IN_PROGRESS.value
        session_model = WorkTimerSession(
            user_id=user.id,
            task_id=task.id,
            status=WorkTimerSessionStatus.RUNNING.value,
            tags_snapshot=list(task.tags or []),
            started_at=now,
        )
        session.add(session_model)
        await session.commit()
        await session.refresh(session_model)
        await repo.update_task(task)
        fresh_task = await repo.get_task_by_id(user.id, task.id)
        return _task_response(fresh_task or task, now)

    if payload.action == "pause":
        running_task_session: WorkTimerSession | None = (
            await repo.get_active_session_for_task(task.id)
        )
        if (
            running_task_session is None
            or running_task_session.status != WorkTimerSessionStatus.RUNNING.value
        ):
            raise ValueError("Сначала запусти таймер")
        interruption = WorkTimerInterruption(
            session_id=running_task_session.id,
            reason=_normalize_text(payload.interruption_reason),
            started_at=now,
        )
        session.add(interruption)
        running_task_session.status = WorkTimerSessionStatus.PAUSED.value
        await session.commit()
        await session.refresh(interruption)
        await session.refresh(running_task_session)
        fresh_task = await repo.get_task_by_id(user.id, task.id)
        return _task_response(fresh_task or task, now)

    if payload.action == "resume":
        paused_task_session: WorkTimerSession | None = (
            await repo.get_active_session_for_task(task.id)
        )
        if (
            paused_task_session is None
            or paused_task_session.status != WorkTimerSessionStatus.PAUSED.value
        ):
            raise ValueError("Сначала поставь таймер на паузу")
        return await _resume_session(session, repo, task, paused_task_session, now)

    if payload.action == "stop":
        stopped_task_session: WorkTimerSession | None = (
            await repo.get_active_session_for_task(task.id)
        )
        if stopped_task_session is None:
            raise ValueError("Сначала запусти таймер")
        return await _stop_session(session, repo, task, stopped_task_session, now)

    raise ValueError("Неизвестное действие таймера")


async def _resume_session(
    session: AsyncSession,
    repo: WorkTimerRepository,
    task: WorkTimerTask,
    session_model: WorkTimerSession,
    now: datetime,
) -> WorkTimerTaskResponse:
    interruption = next(
        (item for item in session_model.interruptions if item.ended_at is None),
        None,
    )
    if interruption is not None:
        interruption.ended_at = now
        await session.commit()
        await session.refresh(interruption)
    session_model.status = WorkTimerSessionStatus.RUNNING.value
    await session.commit()
    await session.refresh(session_model)
    await repo.update_task(task)
    fresh_task = await repo.get_task_by_id(task.user_id, task.id)
    return _task_response(fresh_task or task, now)


async def _stop_session(
    session: AsyncSession,
    repo: WorkTimerRepository,
    task: WorkTimerTask,
    session_model: WorkTimerSession,
    now: datetime,
) -> WorkTimerTaskResponse:
    interruption = next(
        (item for item in session_model.interruptions if item.ended_at is None),
        None,
    )
    if interruption is not None:
        interruption.ended_at = now
        await session.commit()
        await session.refresh(interruption)
    session_model.status = WorkTimerSessionStatus.STOPPED.value
    session_model.ended_at = now
    task.status = WorkTimerTaskStatus.DONE.value
    task.completed_at = now
    await session.commit()
    await session.refresh(session_model)
    await repo.update_task(task)

    journal_payload = ActivityEntryCreateRequest(
        work_date=session_model.started_at.date(),
        activity_type="ticket" if (task.task_ref or "").strip() else "task",
        status="closed",
        title=task.title.strip(),
        description=task.description,
        resolution="Закрыто из рабочего таймера",
        contact=None,
        service=None,
        ticket_number=task.task_ref or None,
        task_url=task.task_url,
        started_at=session_model.started_at.timetz().replace(tzinfo=None),
        ended_at=now.timetz().replace(tzinfo=None),
        ended_date=now.date() if now.date() != session_model.started_at.date() else None,
    )
    await create_activity_entry(session, task.user, journal_payload)

    fresh_task = await repo.get_task_by_id(task.user_id, task.id)
    return _task_response(fresh_task or task, now)


async def list_tasks_as_response(
    session: AsyncSession, user_id: UUID
) -> list[WorkTimerTaskResponse]:
    tasks = await WorkTimerRepository(session).list_tasks(user_id)
    return [_task_response(task) for task in tasks]


async def get_task_response(
    session: AsyncSession, user_id: UUID, task_id: UUID
) -> WorkTimerTaskResponse:
    task = await WorkTimerRepository(session).get_task_by_id(user_id, task_id)
    if task is None:
        raise ValueError("Задача не найдена")
    return _task_response(task)


async def get_weekly_summary(
    session: AsyncSession,
    user_id: UUID,
    week_start: date,
) -> WorkTimerWeeklySummaryResponse:
    repo = WorkTimerRepository(session)
    week_start_dt = datetime(
        week_start.year, week_start.month, week_start.day, tzinfo=UTC
    )
    week_end_dt = week_start_dt + timedelta(days=7)
    week_end = week_start + timedelta(days=6)
    sessions = await repo.list_sessions_for_week(user_id, week_start_dt, week_end_dt)

    total_seconds = 0
    day_totals: dict[date, dict[str, int]] = defaultdict(
        lambda: {"seconds": 0, "sessions": 0, "interruptions": 0}
    )
    task_totals: dict[str, _WeeklyTaskAggregate] = {}
    tag_totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"seconds": 0, "sessions": 0}
    )

    for session_model in sessions:
        duration_seconds = _session_duration_seconds(session_model)
        total_seconds += duration_seconds
        bucket = day_totals[session_model.started_at.date()]
        bucket["seconds"] += duration_seconds
        bucket["sessions"] += 1
        bucket["interruptions"] += len(session_model.interruptions)

        task_bucket = task_totals.setdefault(
            str(session_model.task_id),
            {
                "title": session_model.task.title if session_model.task else "",
                "seconds": 0,
                "sessions": 0,
                "interruptions": 0,
                "tags": list(session_model.tags_snapshot or []),
            },
        )
        task_bucket["seconds"] += duration_seconds
        task_bucket["sessions"] += 1
        task_bucket["interruptions"] += len(session_model.interruptions)
        task_bucket["tags"] = list(session_model.tags_snapshot or [])

        for tag in session_model.tags_snapshot or []:
            tag_bucket = tag_totals[tag]
            tag_bucket["seconds"] += duration_seconds
            tag_bucket["sessions"] += 1

    day_summaries = [
        WorkTimerDaySummary(
            day=day,
            total_seconds=values["seconds"],
            sessions_count=values["sessions"],
            interruptions_count=values["interruptions"],
        )
        for day, values in sorted(day_totals.items(), key=lambda item: item[0])
    ]
    # Заполняем отсутствие дней нулями, чтобы отчёт был визуально цельным.
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        if not any(summary.day == day for summary in day_summaries):
            day_summaries.append(
                WorkTimerDaySummary(
                    day=day,
                    total_seconds=0,
                    sessions_count=0,
                    interruptions_count=0,
                )
            )
    day_summaries.sort(key=lambda item: item.day)

    task_summaries = [
        WorkTimerTaskSummary(
            task_id=task_id,
            title=values["title"],
            total_seconds=values["seconds"],
            sessions_count=values["sessions"],
            interruptions_count=values["interruptions"],
            tags=list(values["tags"]),
        )
        for task_id, values in sorted(
            task_totals.items(), key=lambda item: int(item[1]["seconds"]), reverse=True
        )
    ]
    tag_summaries = [
        WorkTimerTagSummary(
            tag=tag,
            total_seconds=values["seconds"],
            sessions_count=values["sessions"],
        )
        for tag, values in sorted(
            tag_totals.items(), key=lambda item: item[1]["seconds"], reverse=True
        )
    ]

    return WorkTimerWeeklySummaryResponse(
        week_start=week_start,
        week_end=week_end,
        total_seconds=total_seconds,
        days=day_summaries,
        tasks=task_summaries,
        tags=tag_summaries,
        sessions=[_session_response(item) for item in sessions],
    )
