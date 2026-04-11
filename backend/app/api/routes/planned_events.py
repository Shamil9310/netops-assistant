from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.journal import ActivityEntry
from app.models.planned_event import PlannedEvent
from app.schemas.planned_event import (
    PlannedEventCreateRequest,
    PlannedEventResponse,
    PlannedEventUpdateRequest,
)
from app.schemas.journal import ActivityEntryResponse
from app.services import planned_event as event_service

router = APIRouter()


def _to_response(event: PlannedEvent) -> PlannedEventResponse:
    """Преобразует ORM-модель PlannedEvent в схему ответа API."""
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


def _to_activity_entry_response(activity_entry: ActivityEntry) -> ActivityEntryResponse:
    """Преобразует запись журнала в ответ API после конвертации события."""
    return ActivityEntryResponse(
        id=str(activity_entry.id),
        user_id=str(activity_entry.user_id),
        work_date=activity_entry.work_date,
        activity_type=activity_entry.activity_type,  # type: ignore[arg-type]
        status=activity_entry.status,  # type: ignore[arg-type]
        title=activity_entry.title,
        description=activity_entry.description,
        resolution=activity_entry.resolution,
        contact=activity_entry.contact,
        service=activity_entry.service,
        ticket_number=activity_entry.ticket_number,
        task_url=activity_entry.task_url,
        started_at=(
            activity_entry.started_at.timetz().replace(tzinfo=None)
            if activity_entry.started_at
            else None
        ),
        ended_at=(
            activity_entry.finished_at.timetz().replace(tzinfo=None)
            if activity_entry.finished_at
            else None
        ),
        ended_date=(
            activity_entry.finished_at.date() if activity_entry.finished_at else None
        ),
        is_backdated=activity_entry.created_at.date() > activity_entry.work_date,
        created_at=activity_entry.created_at,
        updated_at=activity_entry.updated_at,
    )


@router.get("", response_model=list[PlannedEventResponse])
async def list_events(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    include_completed: bool = Query(default=False),
) -> list[PlannedEventResponse]:
    """Список плановых событий текущего пользователя.

    По умолчанию возвращает только незавершённые события.
    С параметром include_completed=true — включает архивные.
    """
    events = await event_service.list_events(db, current_user.id, include_completed)
    return [_to_response(e) for e in events]


@router.get("/today", response_model=list[PlannedEventResponse])
async def events_today(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[PlannedEventResponse]:
    """Плановые события на сегодня, которые автоматически входят в дневную панель."""
    events = await event_service.list_events_for_today(db, current_user.id)
    return [_to_response(e) for e in events]


@router.post(
    "", response_model=PlannedEventResponse, status_code=status.HTTP_201_CREATED
)
async def create_event(
    payload: PlannedEventCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PlannedEventResponse:
    """Создаёт новое плановое событие."""
    event = await event_service.create_event(
        db,
        user_id=current_user.id,
        event_type=payload.event_type,
        title=payload.title,
        description=payload.description,
        external_ref=payload.external_ref,
        scheduled_at=payload.scheduled_at,
    )
    return _to_response(event)


@router.get("/{event_id}", response_model=PlannedEventResponse)
async def get_event(
    event_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PlannedEventResponse:
    """Возвращает плановое событие по ID. Только владелец."""
    event = await event_service.get_event_by_id(db, event_id, current_user.id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    return _to_response(event)


@router.patch("/{event_id}", response_model=PlannedEventResponse)
async def update_event(
    event_id: UUID,
    payload: PlannedEventUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PlannedEventResponse:
    """Обновляет плановое событие. Только владелец."""
    event = await event_service.get_event_by_id(db, event_id, current_user.id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )

    updated = await event_service.update_event(
        db,
        event=event,
        event_type=payload.event_type,
        title=payload.title,
        description=payload.description,
        external_ref=payload.external_ref,
        scheduled_at=payload.scheduled_at,
        is_completed=payload.is_completed,
        linked_journal_entry_id=payload.linked_journal_entry_id,
    )
    return _to_response(updated)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет плановое событие. Только владелец."""
    event = await event_service.get_event_by_id(db, event_id, current_user.id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    await event_service.delete_event(db, event)


@router.post("/{event_id}/convert-to-journal", response_model=ActivityEntryResponse)
async def convert_event(
    event_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryResponse:
    """Конвертирует плановое событие в запись журнала."""
    event = await event_service.get_event_by_id(db, event_id, current_user.id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    entry = await event_service.convert_event_to_activity_entry(db, event)
    return _to_activity_entry_response(entry)
