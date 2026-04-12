from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.journal import (
    ActivityEntryCreateRequest,
    ActivityEntryListResponse,
    ActivityEntryResponse,
    ActivityEntryUpdateRequest,
    BulkJournalImportRequest,
    BulkJournalImportPreviewResponse,
    BulkJournalImportResponse,
    JournalBulkDeleteResponse,
    JournalDeduplicationResponse,
    JournalSelectedDeleteRequest,
)
from app.services.journal import (
    create_activity_entry,
    delete_activity_entries_for_date,
    delete_all_activity_entries,
    delete_selected_activity_entries,
    delete_duplicate_activity_entries_for_date,
    delete_activity_entry,
    get_activity_entry_by_id,
    import_activity_entries_from_excel_workbook,
    import_activity_entries_from_text,
    list_activity_entries_for_date,
    preview_activity_entries_from_excel_workbook,
    preview_activity_entries_from_text,
    update_activity_entry,
)

router = APIRouter()


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


@router.get("/entries", response_model=ActivityEntryListResponse)
async def get_activity_entries(
    current_user: CurrentUser,
    work_date: date = Query(
        description="Рабочая дата, за которую нужно вернуть записи"
    ),
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryListResponse:
    """Возвращает записи текущего пользователя за выбранную рабочую дату."""
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


@router.post(
    "/entries",
    response_model=ActivityEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_activity_entry(
    payload: ActivityEntryCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryResponse:
    """Создаёт новую запись журнала.

    Ключевая логика:
    пользователь может создать запись за любой work_date,
    и именно по этой дате запись потом попадёт в дневной отчёт.
    """
    try:
        activity_entry = await create_activity_entry(
            session=db,
            user=current_user,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return to_activity_entry_response(activity_entry)


@router.patch("/entries/{entry_id}", response_model=ActivityEntryResponse)
async def patch_activity_entry(
    entry_id: UUID,
    payload: ActivityEntryUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryResponse:
    """Редактирует запись журнала владельца."""
    entry = await get_activity_entry_by_id(db, str(current_user.id), str(entry_id))
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена"
        )

    try:
        updated = await update_activity_entry(db, entry, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return to_activity_entry_response(updated)


@router.get("/entries/{entry_id}", response_model=ActivityEntryResponse)
async def get_activity_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ActivityEntryResponse:
    """Возвращает одну запись журнала владельца."""
    entry = await get_activity_entry_by_id(db, str(current_user.id), str(entry_id))
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена"
        )
    return to_activity_entry_response(entry)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_activity_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет запись журнала владельца."""
    entry = await get_activity_entry_by_id(db, str(current_user.id), str(entry_id))
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена"
        )
    await delete_activity_entry(db, entry)


@router.post("/entries/delete-for-date", response_model=JournalBulkDeleteResponse)
async def remove_activity_entries_for_date(
    current_user: CurrentUser,
    work_date: date = Query(
        description="Рабочая дата, за которую нужно удалить все записи"
    ),
    db: AsyncSession = Depends(get_db),
) -> JournalBulkDeleteResponse:
    """Удаляет все записи текущего пользователя за выбранную рабочую дату."""
    removed_count = await delete_activity_entries_for_date(
        session=db,
        user_id=str(current_user.id),
        work_date=work_date,
    )
    return JournalBulkDeleteResponse(
        scope="work_date",
        removed=removed_count,
        work_date=work_date,
    )


@router.post("/entries/delete-all", response_model=JournalBulkDeleteResponse)
async def remove_all_activity_entries(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> JournalBulkDeleteResponse:
    """Удаляет все записи журнала текущего пользователя."""
    removed_count = await delete_all_activity_entries(
        session=db,
        user_id=str(current_user.id),
    )
    return JournalBulkDeleteResponse(
        scope="all",
        removed=removed_count,
        work_date=None,
    )


@router.post("/entries/delete-selected", response_model=JournalBulkDeleteResponse)
async def remove_selected_activity_entries(
    payload: JournalSelectedDeleteRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> JournalBulkDeleteResponse:
    """Удаляет только выбранные записи журнала текущего пользователя."""
    removed_count = await delete_selected_activity_entries(
        session=db,
        user_id=str(current_user.id),
        entry_ids=payload.entry_ids,
    )
    return JournalBulkDeleteResponse(
        scope="selected",
        removed=removed_count,
        work_date=None,
    )


@router.post("/entries/deduplicate", response_model=JournalDeduplicationResponse)
async def deduplicate_activity_entries(
    current_user: CurrentUser,
    work_date: date = Query(
        description="Рабочая дата, в рамках которой нужно удалить дубли"
    ),
    db: AsyncSession = Depends(get_db),
) -> JournalDeduplicationResponse:
    """Удаляет дубли журналa текущего пользователя за выбранную рабочую дату."""
    removed_count, duplicate_ticket_numbers = (
        await delete_duplicate_activity_entries_for_date(
            session=db,
            user_id=str(current_user.id),
            work_date=work_date,
        )
    )
    return JournalDeduplicationResponse(
        work_date=work_date,
        removed=removed_count,
        duplicate_ticket_numbers=duplicate_ticket_numbers,
    )


@router.post(
    "/entries/import",
    response_model=BulkJournalImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_activity_entries(
    payload: BulkJournalImportRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BulkJournalImportResponse:
    """Импортирует несколько записей журнала из текста."""
    try:
        created_entries, warnings = await import_activity_entries_from_text(
            session=db,
            user=current_user,
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return BulkJournalImportResponse(
        created=len(created_entries),
        items=[to_activity_entry_response(entry) for entry in created_entries],
        warnings=warnings,
    )


@router.post("/entries/import/preview", response_model=BulkJournalImportPreviewResponse)
async def preview_activity_entries(
    _: CurrentUser,
    payload: BulkJournalImportRequest,
    db: AsyncSession = Depends(get_db),
) -> BulkJournalImportPreviewResponse:
    """Показывает, как текст будет распознан, без сохранения в базу."""
    preview_items, warnings = preview_activity_entries_from_text(payload)
    return BulkJournalImportPreviewResponse(
        total=len(preview_items),
        items=preview_items,
        warnings=warnings,
    )


@router.post(
    "/entries/import/excel",
    response_model=BulkJournalImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_activity_entries_from_excel(
    current_user: CurrentUser,
    file: Annotated[UploadFile, File(description="Excel-файл с выгрузкой обращений")],
    db: AsyncSession = Depends(get_db),
) -> BulkJournalImportResponse:
    """Импортирует записи журнала из Excel-файла."""
    workbook_bytes = await file.read()

    try:
        created_entries, warnings = await import_activity_entries_from_excel_workbook(
            session=db,
            user=current_user,
            workbook_bytes=workbook_bytes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return BulkJournalImportResponse(
        created=len(created_entries),
        items=[to_activity_entry_response(entry) for entry in created_entries],
        warnings=warnings,
    )


@router.post(
    "/entries/import/excel/preview",
    response_model=BulkJournalImportPreviewResponse,
)
async def preview_activity_entries_from_excel(
    _: CurrentUser,
    file: Annotated[UploadFile, File(description="Excel-файл с выгрузкой обращений")],
    db: AsyncSession = Depends(get_db),
) -> BulkJournalImportPreviewResponse:
    """Показывает предпросмотр Excel-импорта без сохранения в базу."""
    workbook_bytes = await file.read()

    try:
        preview_items, warnings = preview_activity_entries_from_excel_workbook(
            workbook_bytes=workbook_bytes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return BulkJournalImportPreviewResponse(
        total=len(preview_items),
        items=preview_items,
        warnings=warnings,
    )
