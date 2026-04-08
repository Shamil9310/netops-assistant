from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.journal import ActivityStatus, ActivityType
from app.models.journal import ActivityEntry
from app.schemas.journal import ActivityEntryResponse
from app.schemas.search import ArchiveResponse, SearchResponse
from app.services.search import get_archive_entries, search_entries

router = APIRouter()


def _to_response(entry: ActivityEntry) -> ActivityEntryResponse:
    """Преобразует ORM-объект записи журнала в API-схему."""
    return ActivityEntryResponse(
        id=str(entry.id),
        user_id=str(entry.user_id),
        work_date=entry.work_date,
        activity_type=entry.activity_type,
        status=entry.status,
        title=entry.title,
        description=entry.description,
        ticket_number=entry.ticket_number or entry.external_ref,
        started_at=(
            entry.started_at.timetz().replace(tzinfo=None) if entry.started_at else None
        ),
        ended_at=(
            entry.finished_at.timetz().replace(tzinfo=None)
            if entry.finished_at
            else None
        ),
        is_backdated=entry.created_at.date() > entry.work_date,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("", response_model=SearchResponse)
async def search(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(
        default=None,
        description="Полнотекстовый поиск по title/description/external_ref",
    ),
    activity_type: ActivityType | None = Query(default=None),
    activity_status: ActivityStatus | None = Query(default=None, alias="status"),
    external_ref: str | None = Query(default=None),
    ticket_number: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    """Поиск по журналу с полнотекстовым и структурным фильтром.

    Параметр `q` ищет подстроку в title, description и external_ref (case-insensitive).
    Все остальные параметры — структурные фильтры, применяются вместе с `q`.
    """
    try:
        results, total = await search_entries(
            db,
            user_id=current_user.id,
            query=q,
            activity_type=activity_type,
            status=activity_status,
            external_ref=external_ref,
            ticket_number=ticket_number,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error
    return SearchResponse(
        total=total,
        limit=limit,
        offset=offset,
        results=[_to_response(e) for e in results],
    )


@router.get("/archive", response_model=ArchiveResponse)
async def archive(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None, description="Полнотекстовый поиск по архиву"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    activity_type: ActivityType | None = Query(default=None),
    external_ref: str | None = Query(default=None),
    ticket_number: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ArchiveResponse:
    """Архив завершённых и отменённых записей журнала.

    Показывает только CLOSED и CANCELLED записи — исторические данные.
    Поддерживает фильтрацию по периоду, типу активности, external_ref.
    """
    try:
        results, total = await get_archive_entries(
            db,
            user_id=current_user.id,
            query=q,
            date_from=date_from,
            date_to=date_to,
            activity_type=activity_type,
            external_ref=external_ref,
            ticket_number=ticket_number,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error
    return ArchiveResponse(
        total=total,
        limit=limit,
        offset=offset,
        results=[_to_response(e) for e in results],
    )
