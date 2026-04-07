from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.journal import (
    ActivityEntryCreateRequest,
    ActivityEntryListResponse,
    ActivityEntryResponse,
    ActivityEntryUpdateRequest,
)
from app.services.auth import get_current_user
from app.services.journal import (
    create_activity_entry,
    delete_activity_entry,
    get_activity_entry_by_id,
    list_activity_entries_for_date,
    update_activity_entry,
)

router = APIRouter()


async def require_authenticated_user(
    request: Request,
    session: AsyncSession,
):
    """Возвращает текущего пользователя или поднимает 401.

    Отдельная функция нужна затем, чтобы journal API не дублировал
    авторизационную проверку в каждом endpoint.
    """
    session_token = request.cookies.get(settings.session_cookie_name)
    current_user = await get_current_user(session, session_token)

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )

    return current_user


def to_activity_entry_response(activity_entry) -> ActivityEntryResponse:
    """Преобразует ORM-модель в API-схему."""
    return ActivityEntryResponse(
        id=str(activity_entry.id),
        user_id=str(activity_entry.user_id),
        work_date=activity_entry.work_date,
        activity_type=activity_entry.activity_type,
        status=activity_entry.status,
        title=activity_entry.title,
        description=activity_entry.description,
        ticket_number=activity_entry.ticket_number,
        started_at=activity_entry.started_at.timetz().replace(tzinfo=None) if activity_entry.started_at else None,
        ended_at=activity_entry.finished_at.timetz().replace(tzinfo=None) if activity_entry.finished_at else None,
        is_backdated=activity_entry.created_at.date() > activity_entry.work_date,
        created_at=activity_entry.created_at,
        updated_at=activity_entry.updated_at,
    )


@router.get("/entries", response_model=ActivityEntryListResponse)
async def get_activity_entries(
    request: Request,
    work_date: date = Query(description="Рабочая дата, за которую нужно вернуть записи"),
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryListResponse:
    """Возвращает записи текущего пользователя за выбранную рабочую дату."""
    current_user = await require_authenticated_user(request, db)
    activity_entries = await list_activity_entries_for_date(
        session=db,
        user_id=str(current_user.id),
        work_date=work_date,
    )

    return ActivityEntryListResponse(
        work_date=work_date,
        total=len(activity_entries),
        items=[to_activity_entry_response(entry) for entry in activity_entries],
    )


@router.post("/entries", response_model=ActivityEntryResponse, status_code=status.HTTP_201_CREATED)
async def post_activity_entry(
    payload: ActivityEntryCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryResponse:
    """Создаёт новую запись журнала.

    Ключевая логика:
    пользователь может создать запись за любой work_date,
    и именно по этой дате запись потом попадёт в дневной отчёт.
    """
    current_user = await require_authenticated_user(request, db)
    activity_entry = await create_activity_entry(
        session=db,
        user=current_user,
        payload=payload,
    )

    return to_activity_entry_response(activity_entry)


@router.patch("/entries/{entry_id}", response_model=ActivityEntryResponse)
async def patch_activity_entry(
    entry_id: UUID,
    payload: ActivityEntryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryResponse:
    """Редактирует запись журнала владельца."""
    current_user = await require_authenticated_user(request, db)
    entry = await get_activity_entry_by_id(db, str(current_user.id), str(entry_id))
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")

    updated = await update_activity_entry(db, entry, payload)
    return to_activity_entry_response(updated)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_activity_entry(
    entry_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет запись журнала владельца."""
    current_user = await require_authenticated_user(request, db)
    entry = await get_activity_entry_by_id(db, str(current_user.id), str(entry_id))
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
    await delete_activity_entry(db, entry)
