from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.config import settings
from app.db.session import get_db
from app.models.journal import ActivityEntry
from app.models.report_record import ReportRecord, ReportStatus, ReportType
from app.schemas.reports import (
    DailyReportRequest,
    RangeReportRequest,
    ReportPreviewResponse,
    ReportRecordResponse,
    WeeklyReportRequest,
)
from app.services.access_audit import log_access_event
from app.services.export import calculate_export_expiration, render_docx_bytes, render_pdf_bytes, strip_markdown
from app.services.reports import (
    format_report_content,
    generate_daily_report,
    generate_night_work_result_report,
    generate_range_report,
    generate_weekly_report,
)

router = APIRouter()


async def _save_report(
    session: AsyncSession,
    user_id: UUID,
    report_type: ReportType,
    period_from: str,
    period_to: str,
    content_md: str,
) -> ReportRecord:
    """Сохраняет сгенерированный отчёт в историю."""
    record = ReportRecord(
        user_id=user_id,
        report_type=report_type.value,
        report_status=ReportStatus.DRAFT.value,
        period_from=period_from,
        period_to=period_to,
        content_md=content_md,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


def _to_preview(record: ReportRecord, updates_after_finalization: int = 0) -> ReportPreviewResponse:
    return ReportPreviewResponse(
        report_id=str(record.id),
        report_type=record.report_type,
        report_status=record.report_status,
        period_from=record.period_from,
        period_to=record.period_to,
        content_md=record.content_md,
        generated_at=record.created_at,
        updates_after_finalization=updates_after_finalization,
    )


def _to_record_response(record: ReportRecord) -> ReportRecordResponse:
    return ReportRecordResponse(
        id=str(record.id),
        report_type=record.report_type,
        report_status=record.report_status,
        period_from=record.period_from,
        period_to=record.period_to,
        generated_at=record.created_at,
    )


# ---------------------------------------------------------------------------
# Генерация отчётов
# ---------------------------------------------------------------------------


@router.post("/daily", response_model=ReportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def generate_daily(
    payload: DailyReportRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Генерирует дневной отчёт и сохраняет в историю."""
    content = await generate_daily_report(
        db,
        user_id=current_user.id,
        report_date=payload.report_date,
        author_name=current_user.full_name,
    )
    try:
        content = format_report_content(content, payload.format_profile)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    date_str = payload.report_date.isoformat()
    record = await _save_report(db, current_user.id, ReportType.DAILY, date_str, date_str, content)
    return _to_preview(record)


@router.post("/weekly", response_model=ReportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def generate_weekly(
    payload: WeeklyReportRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Генерирует недельный отчёт (7 дней с week_start) и сохраняет в историю."""
    from datetime import timedelta

    week_end = payload.week_start + timedelta(days=6)
    content = await generate_weekly_report(
        db,
        user_id=current_user.id,
        week_start=payload.week_start,
        author_name=current_user.full_name,
    )
    try:
        content = format_report_content(content, payload.format_profile)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    record = await _save_report(
        db,
        current_user.id,
        ReportType.WEEKLY,
        payload.week_start.isoformat(),
        week_end.isoformat(),
        content,
    )
    return _to_preview(record)


@router.post("/range", response_model=ReportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def generate_range(
    payload: RangeReportRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Генерирует отчёт за произвольный период и сохраняет в историю."""
    if payload.date_to < payload.date_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_to не может быть раньше date_from",
        )
    content = await generate_range_report(
        db,
        user_id=current_user.id,
        date_from=payload.date_from,
        date_to=payload.date_to,
        author_name=current_user.full_name,
    )
    try:
        content = format_report_content(content, payload.format_profile)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    record = await _save_report(
        db,
        current_user.id,
        ReportType.RANGE,
        payload.date_from.isoformat(),
        payload.date_to.isoformat(),
        content,
    )
    return _to_preview(record)


@router.post("/night-work/{plan_id}", response_model=ReportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def generate_night_work_result(
    plan_id: UUID,
    current_user: CurrentUser,
    format_profile: str = Query(default="engineer", pattern="^(engineer|manager)$"),
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Генерирует итоговый отчёт ночных работ и сохраняет в историю."""
    try:
        content = await generate_night_work_result_report(
            db,
            user_id=current_user.id,
            plan_id=plan_id,
            author_name=current_user.full_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    content = format_report_content(content, format_profile)

    period_value = datetime.now(UTC).date().isoformat()
    record = await _save_report(
        db,
        current_user.id,
        ReportType.NIGHT_WORK_RESULT,
        period_value,
        period_value,
        content,
    )
    return _to_preview(record)


# ---------------------------------------------------------------------------
# История и экспорт
# ---------------------------------------------------------------------------


@router.get("/history", response_model=list[ReportRecordResponse])
async def report_history(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[ReportRecordResponse]:
    """История сгенерированных отчётов текущего пользователя (без контента)."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.user_id == current_user.id)
        .order_by(ReportRecord.created_at.desc())
        .limit(100)
    )
    records = list(result.scalars().all())
    return [_to_record_response(r) for r in records]


@router.get("/{report_id}", response_model=ReportPreviewResponse)
async def get_report(
    report_id: UUID,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Возвращает сохранённый отчёт с контентом по ID."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    await log_access_event(
        db,
        user_id=current_user.id,
        resource_type="report",
        resource_id=str(record.id),
        action="preview",
        request_id=getattr(request.state, "request_id", None),
    )
    updates_after_finalization = 0
    if record.report_status == ReportStatus.FINAL.value:
        updates_after_finalization = await _count_updates_after_finalization(db, record)
    return _to_preview(record, updates_after_finalization=updates_after_finalization)


@router.post("/{report_id}/refresh", response_model=ReportPreviewResponse)
async def refresh_report(
    report_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Пересобирает draft-отчёт по сохранённому типу и периоду."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    if record.report_status != ReportStatus.DRAFT.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Можно обновлять только draft отчёт")

    period_from = datetime.fromisoformat(record.period_from).date()
    period_to = datetime.fromisoformat(record.period_to).date()

    if record.report_type == ReportType.DAILY.value:
        refreshed = await generate_daily_report(
            db,
            user_id=current_user.id,
            report_date=period_from,
            author_name=current_user.full_name,
        )
    elif record.report_type == ReportType.WEEKLY.value:
        refreshed = await generate_weekly_report(
            db,
            user_id=current_user.id,
            week_start=period_from,
            author_name=current_user.full_name,
        )
    elif record.report_type == ReportType.RANGE.value:
        refreshed = await generate_range_report(
            db,
            user_id=current_user.id,
            date_from=period_from,
            date_to=period_to,
            author_name=current_user.full_name,
        )
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Этот тип отчёта не поддерживает refresh")

    record.content_md = refreshed
    await db.commit()
    await db.refresh(record)
    return _to_preview(record)


@router.post("/{report_id}/finalize", response_model=ReportPreviewResponse)
async def finalize_report(
    report_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Фиксирует отчёт в статус final."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    record.report_status = ReportStatus.FINAL.value
    await db.commit()
    await db.refresh(record)
    return _to_preview(record, updates_after_finalization=0)


@router.post("/{report_id}/regenerate-draft", response_model=ReportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def regenerate_draft_from_final(
    report_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReportPreviewResponse:
    """Создаёт новую draft-версию из final-отчёта с актуальными данными периода.

    Важное бизнес-правило:
    final-отчёт остаётся неизменным snapshot-документом.
    Пересборка выполняется в новый draft, чтобы пользователь мог сравнить
    и осознанно принять новую версию.
    """
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    source_record = result.scalar_one_or_none()
    if source_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    if source_record.report_status != ReportStatus.FINAL.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пересборка доступна только для final отчёта")

    period_from = datetime.fromisoformat(source_record.period_from).date()
    period_to = datetime.fromisoformat(source_record.period_to).date()

    if source_record.report_type == ReportType.DAILY.value:
        content_md = await generate_daily_report(
            db,
            user_id=current_user.id,
            report_date=period_from,
            author_name=current_user.full_name,
        )
    elif source_record.report_type == ReportType.WEEKLY.value:
        content_md = await generate_weekly_report(
            db,
            user_id=current_user.id,
            week_start=period_from,
            author_name=current_user.full_name,
        )
    elif source_record.report_type == ReportType.RANGE.value:
        content_md = await generate_range_report(
            db,
            user_id=current_user.id,
            date_from=period_from,
            date_to=period_to,
            author_name=current_user.full_name,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Для этого типа отчёта пересборка draft не поддерживается",
        )

    draft_record = await _save_report(
        db,
        user_id=current_user.id,
        report_type=ReportType(source_record.report_type),
        period_from=source_record.period_from,
        period_to=source_record.period_to,
        content_md=content_md,
    )
    return _to_preview(draft_record, updates_after_finalization=0)


@router.get("/{report_id}/export/md")
async def export_md(
    report_id: UUID,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Экспортирует отчёт как Markdown-файл (.md)."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    await log_access_event(
        db,
        user_id=current_user.id,
        resource_type="report",
        resource_id=str(record.id),
        action="export_md",
        request_id=getattr(request.state, "request_id", None),
    )

    filename = f"report_{record.period_from}_{record.period_to}.md"
    return Response(
        content=record.content_md.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}/export/txt")
async def export_txt(
    report_id: UUID,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Экспортирует отчёт как текстовый файл (.txt) без Markdown-разметки."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    await log_access_event(
        db,
        user_id=current_user.id,
        resource_type="report",
        resource_id=str(record.id),
        action="export_txt",
        request_id=getattr(request.state, "request_id", None),
    )

    # Убираем Markdown-разметку для plain text экспорта.
    plain_text = strip_markdown(record.content_md)
    filename = f"report_{record.period_from}_{record.period_to}.txt"
    return Response(
        content=plain_text.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}/export/docx")
async def export_docx(
    report_id: UUID,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Экспортирует отчёт как DOCX-файл."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    await log_access_event(
        db,
        user_id=current_user.id,
        resource_type="report",
        resource_id=str(record.id),
        action="export_docx",
        request_id=getattr(request.state, "request_id", None),
    )

    filename = f"report_{record.period_from}_{record.period_to}.docx"
    return Response(
        content=render_docx_bytes(record.content_md),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}/export/pdf")
async def export_pdf(
    report_id: UUID,
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Экспортирует отчёт как PDF-файл."""
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.id == report_id)
        .where(ReportRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден")
    await log_access_event(
        db,
        user_id=current_user.id,
        resource_type="report",
        resource_id=str(record.id),
        action="export_pdf",
        request_id=getattr(request.state, "request_id", None),
    )

    filename = f"report_{record.period_from}_{record.period_to}.pdf"
    return Response(
        content=render_pdf_bytes(record.content_md),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/registry", response_model=list[ReportRecordResponse])
async def export_registry(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ReportRecordResponse]:
    """Возвращает реестр экспортируемых отчётов по retention policy.

    На текущем этапе retention применяется как отображаемое правило:
    запись считается актуальной до `created_at + export_retention_days`.
    """
    result = await db.execute(
        select(ReportRecord)
        .where(ReportRecord.user_id == current_user.id)
        .order_by(ReportRecord.created_at.desc())
        .limit(limit)
    )
    records = list(result.scalars().all())

    now = datetime.now(UTC)
    registry_records: list[ReportRecordResponse] = []
    for record in records:
        expires_at = calculate_export_expiration(record.created_at, settings.export_retention_days)
        if expires_at >= now:
            registry_records.append(_to_record_response(record))
    return registry_records


async def _count_updates_after_finalization(session: AsyncSession, report: ReportRecord) -> int:
    """Считает новые записи журнала после финализации отчёта."""
    period_from = datetime.fromisoformat(report.period_from).date()
    period_to = datetime.fromisoformat(report.period_to).date()
    result = await session.execute(
        select(func.count(ActivityEntry.id))
        .where(ActivityEntry.user_id == report.user_id)
        .where(ActivityEntry.work_date >= period_from)
        .where(ActivityEntry.work_date <= period_to)
        .where(ActivityEntry.created_at > report.created_at)
    )
    count_value = result.scalar_one()
    return int(count_value)
