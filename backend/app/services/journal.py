from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import ActivityEntry
from app.models.user import User
from app.schemas.journal import ActivityEntryCreateRequest, ActivityEntryUpdateRequest


async def list_activity_entries_for_date(
    session: AsyncSession,
    user_id: str,
    work_date: date,
) -> list[ActivityEntry]:
    """Возвращает записи пользователя за конкретную рабочую дату.

    Почему фильтрация идёт именно по user_id + work_date:
    - пользователь должен видеть только свои записи;
    - одна и та же дата может дополняться позже;
    - отчёт за день строится по work_date, а не по created_at.
    """
    statement: Select[tuple[ActivityEntry]] = (
        select(ActivityEntry)
        .where(ActivityEntry.user_id == user_id)
        .where(ActivityEntry.work_date == work_date)
        .order_by(
            ActivityEntry.started_at.asc().nullslast(), ActivityEntry.created_at.asc()
        )
    )

    result = await session.execute(statement)
    return list(result.scalars().all())


async def create_activity_entry(
    session: AsyncSession,
    user: User,
    payload: ActivityEntryCreateRequest,
) -> ActivityEntry:
    """Создаёт новую запись журнала для текущего пользователя.

    Логика работы с датами:
    - work_date отвечает за день, к которому запись относится в отчётах;
    - ended_date отвечает за реальную дату закрытия задачи;
    - если ended_date не передана, считаем, что запись закрыта в work_date.
    """
    effective_ended_date = payload.ended_date or payload.work_date
    if effective_ended_date < payload.work_date:
        raise ValueError("Дата окончания не может быть раньше рабочей даты")

    started_at_value = payload.started_at
    if started_at_value is None:
        started_at_value = await _get_last_finished_time_for_date(
            session=session,
            user_id=user.id,
            work_date=payload.work_date,
        )

    started_at_dt = _combine_work_date_and_time(payload.work_date, started_at_value)
    ended_at_dt = _combine_work_date_and_time(effective_ended_date, payload.ended_at)

    activity_entry = ActivityEntry(
        user_id=user.id,
        work_date=payload.work_date,
        activity_type=payload.activity_type,
        status=payload.status,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        resolution=payload.resolution.strip() if payload.resolution else None,
        contact=payload.contact.strip() if payload.contact else None,
        external_ref=payload.ticket_number.strip() if payload.ticket_number else None,
        ticket_number=payload.ticket_number.strip() if payload.ticket_number else None,
        task_url=payload.task_url.strip() if payload.task_url else None,
        started_at=started_at_dt,
        finished_at=ended_at_dt,
    )

    session.add(activity_entry)
    await session.commit()
    await session.refresh(activity_entry)

    return activity_entry


async def get_activity_entry_by_id(
    session: AsyncSession,
    user_id: str,
    entry_id: str,
) -> ActivityEntry | None:
    """Возвращает запись по ID в рамках пользователя-владельца."""
    result = await session.execute(
        select(ActivityEntry)
        .where(ActivityEntry.user_id == user_id)
        .where(ActivityEntry.id == entry_id)
    )
    return result.scalar_one_or_none()


async def update_activity_entry(
    session: AsyncSession,
    entry: ActivityEntry,
    payload: ActivityEntryUpdateRequest,
) -> ActivityEntry:
    """Обновляет запись журнала по переданным полям.

    При обновлении важно сначала вычислить итоговые значения даты и времени,
    а уже потом проверять ограничения. Иначе можно пропустить некорректную
    комбинацию полей, если часть значений пришла в запросе, а часть осталась
    в существующей записи.
    """
    if payload.work_date is not None:
        entry.work_date = payload.work_date
    if payload.activity_type is not None:
        entry.activity_type = payload.activity_type
    if payload.status is not None:
        entry.status = payload.status
    if payload.title is not None:
        entry.title = payload.title.strip()
    if payload.description is not None:
        entry.description = payload.description.strip() if payload.description else None
    if payload.resolution is not None:
        entry.resolution = payload.resolution.strip() if payload.resolution else None
    if payload.contact is not None:
        entry.contact = payload.contact.strip() if payload.contact else None
    if payload.ticket_number is not None:
        normalized_ticket = (
            payload.ticket_number.strip() if payload.ticket_number else None
        )
        entry.ticket_number = normalized_ticket
        entry.external_ref = normalized_ticket
    if payload.task_url is not None:
        entry.task_url = payload.task_url.strip() if payload.task_url else None

    effective_work_date = (
        payload.work_date if payload.work_date is not None else entry.work_date
    )
    effective_ended_date = (
        payload.ended_date
        if payload.ended_date is not None
        else (
            entry.finished_at.date()
            if entry.finished_at is not None
            else effective_work_date
        )
    )
    effective_started_time = (
        payload.started_at
        if payload.started_at is not None
        else (
            entry.started_at.timetz().replace(tzinfo=None)
            if entry.started_at is not None
            else None
        )
    )
    effective_ended_time = (
        payload.ended_at
        if payload.ended_at is not None
        else (
            entry.finished_at.timetz().replace(tzinfo=None)
            if entry.finished_at is not None
            else None
        )
    )
    if effective_ended_date < effective_work_date:
        raise ValueError("Дата окончания не может быть раньше рабочей даты")
    if (
        effective_started_time is not None
        and effective_ended_time is not None
        and effective_ended_date == effective_work_date
        and effective_ended_time < effective_started_time
    ):
        raise ValueError("Время окончания не может быть раньше времени начала")

    if payload.started_at is not None:
        entry.started_at = _combine_work_date_and_time(
            effective_work_date, payload.started_at
        )
    if payload.ended_at is not None:
        entry.finished_at = _combine_work_date_and_time(
            effective_ended_date, payload.ended_at
        )
    elif payload.ended_date is not None and entry.finished_at is not None:
        entry.finished_at = _combine_work_date_and_time(
            effective_ended_date, entry.finished_at.timetz().replace(tzinfo=None)
        )

    await session.commit()
    await session.refresh(entry)
    return entry


async def delete_activity_entry(session: AsyncSession, entry: ActivityEntry) -> None:
    """Удаляет запись журнала."""
    await session.delete(entry)
    await session.commit()


async def list_entries_for_date(
    session: AsyncSession,
    user_id: UUID,
    day_start: datetime,
    day_end: datetime,
) -> list[ActivityEntry]:
    """Возвращает записи за период по рабочей дате.

    Здесь фильтруем именно по work_date, а не по времени создания записи.
    Это важно, потому что сотрудник может занести запись позже, но она всё равно
    должна попасть в отчёт за исходную рабочую дату.
    """
    result = await session.execute(
        select(ActivityEntry)
        .where(ActivityEntry.user_id == user_id)
        .where(ActivityEntry.work_date >= day_start.date())
        .where(ActivityEntry.work_date <= day_end.date())
        .order_by(
            ActivityEntry.work_date.asc(),
            ActivityEntry.started_at.asc().nullslast(),
            ActivityEntry.created_at.asc(),
        )
    )
    return list(result.scalars().all())


def _combine_work_date_and_time(work_date: date, value: time | None) -> datetime | None:
    """Объединяет дату и время в одно значение для сохранения в базе."""
    if value is None:
        return None
    return datetime.combine(work_date, value, tzinfo=UTC)


async def _get_last_finished_time_for_date(
    session: AsyncSession,
    user_id: UUID,
    work_date: date,
) -> time | None:
    """Возвращает время завершения последней записи за рабочую дату.

    Это нужно для автоподстановки времени начала в форме:
    следующая запись часто начинается сразу после предыдущей.
    """
    result = await session.execute(
        select(ActivityEntry.finished_at)
        .where(ActivityEntry.user_id == user_id)
        .where(ActivityEntry.work_date == work_date)
        .where(ActivityEntry.finished_at.is_not(None))
        .order_by(ActivityEntry.finished_at.desc(), ActivityEntry.created_at.desc())
        .limit(1)
    )
    finished_at = result.scalar_one_or_none()
    if finished_at is None:
        return None
    return finished_at.timetz().replace(tzinfo=None)
